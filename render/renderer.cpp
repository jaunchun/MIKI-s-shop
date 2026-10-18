#include <GL/glew.h>
#include <glm/gtc/matrix_transform.hpp>
#include <algorithm>
#include <cmath>
#include <stdexcept>
#include "renderer.h"

namespace {

// ---------- scene pass: runs at low resolution ----------
const char* kSceneVS = R"GLSL(
#version 330 core
layout(location = 0) in vec3 aPos;
layout(location = 1) in vec3 aNormal;
uniform mat4 uModel;
uniform mat4 uView;
uniform mat4 uProj;
uniform vec2 uRes;
out vec3 vWorldPos;
out vec3 vNormal;
void main() {
    vec4 world = uModel * vec4(aPos, 1.0);
    vec4 clip = uProj * uView * world;
    // PS1-style vertex snapping: lock vertices to the low-res pixel grid
    vec3 ndc = clip.xyz / clip.w;
    ndc.xy = round(ndc.xy * uRes * 0.5) / (uRes * 0.5);
    gl_Position = vec4(ndc * clip.w, clip.w);
    vWorldPos = world.xyz;
    vNormal = mat3(transpose(inverse(uModel))) * aNormal;
}
)GLSL";

const char* kSceneFS = R"GLSL(
#version 330 core
in vec3 vWorldPos;
in vec3 vNormal;
uniform vec3 uColor;
uniform vec3 uCamPos;
uniform vec3 uCamDir;
uniform vec3 uAmbient;
uniform vec3 uFogColor;
uniform float uFogDensity;
uniform int uFlashlight;
out vec4 FragColor;
void main() {
    vec3 n = normalize(vNormal);
    vec3 toFrag = vWorldPos - uCamPos;
    float dist = length(toFrag);
    vec3 dir = toFrag / max(dist, 0.0001);

    vec3 light = uAmbient;
    if (uFlashlight == 1) {
        float cosAng = dot(dir, uCamDir);
        float cone = smoothstep(0.82, 0.93, cosAng);
        float atten = 1.0 / (1.0 + 0.15 * dist + 0.05 * dist * dist);
        float diff = max(dot(n, -dir), 0.0);
        light += vec3(1.0, 0.95, 0.8) * cone * atten * diff * 1.8;
    }

    vec3 color = uColor * light;
    float fog = 1.0 - exp(-(uFogDensity * dist) * (uFogDensity * dist));
    color = mix(color, uFogColor, clamp(fog, 0.0, 1.0));
    FragColor = vec4(color, 1.0);
}
)GLSL";

// ---------- post pass: upscale + dither + colour quantise + vignette ----------
const char* kPostVS = R"GLSL(
#version 330 core
out vec2 vUV;
void main() {
    vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2);
    vUV = p;
    gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0);
}
)GLSL";

const char* kPostFS = R"GLSL(
#version 330 core
in vec2 vUV;
uniform sampler2D uTex;
uniform vec2 uRes;
out vec4 FragColor;
const float bayer[16] = float[16](0.0, 8.0, 2.0, 10.0,
                                  12.0, 4.0, 14.0, 6.0,
                                  3.0, 11.0, 1.0, 9.0,
                                  15.0, 7.0, 13.0, 5.0);
void main() {
    vec3 c = texture(uTex, vUV).rgb;
    ivec2 px = ivec2(vUV * uRes);
    float d = (bayer[(px.y & 3) * 4 + (px.x & 3)] / 16.0 - 0.5) / 32.0;
    c += d;
    c = floor(c * 32.0 + 0.5) / 32.0;
    float v = 1.0 - smoothstep(0.35, 0.85, length(vUV - 0.5));
    c *= mix(0.45, 1.0, v);
    FragColor = vec4(c, 1.0);
}
)GLSL";

glm::vec3 to_glm(const Vec3& a) { return {a[0], a[1], a[2]}; }

}  // namespace

Renderer::Renderer(int low_w, int low_h) : low_w_(low_w), low_h_(low_h) {
    scene_ = std::make_unique<Shader>(kSceneVS, kSceneFS);
    post_ = std::make_unique<Shader>(kPostVS, kPostFS);

    glGenFramebuffers(1, &fbo_);
    glBindFramebuffer(GL_FRAMEBUFFER, fbo_);

    glGenTextures(1, &color_tex_);
    glBindTexture(GL_TEXTURE_2D, color_tex_);
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, low_w_, low_h_, 0, GL_RGBA, GL_UNSIGNED_BYTE, nullptr);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST);  // crisp pixels
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE);
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE);
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, color_tex_, 0);

    glGenRenderbuffers(1, &depth_rb_);
    glBindRenderbuffer(GL_RENDERBUFFER, depth_rb_);
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT24, low_w_, low_h_);
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, depth_rb_);

    if (glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE)
        throw std::runtime_error("low-res framebuffer is incomplete");
    glBindFramebuffer(GL_FRAMEBUFFER, 0);

    glGenVertexArrays(1, &empty_vao_);  // fullscreen triangle needs no vertex data
}

Renderer::~Renderer() {
    if (empty_vao_) glDeleteVertexArrays(1, &empty_vao_);
    if (depth_rb_) glDeleteRenderbuffers(1, &depth_rb_);
    if (color_tex_) glDeleteTextures(1, &color_tex_);
    if (fbo_) glDeleteFramebuffers(1, &fbo_);
}

Handle Renderer::load_mesh(const std::string& name) {
    auto it = mesh_cache_.find(name);
    if (it != mesh_cache_.end()) return it->second;

    std::unique_ptr<Mesh> m;
    if (name == "cube") m = Mesh::cube();
    else if (name == "plane") m = Mesh::plane();
    else m = Mesh::from_obj(name);

    meshes_.push_back(std::move(m));
    Handle h = static_cast<Handle>(meshes_.size());  // 1-based
    mesh_cache_[name] = h;
    return h;
}

Handle Renderer::create_object(Handle mesh, Vec3 color) {
    if (mesh == 0 || mesh > meshes_.size()) throw std::out_of_range("invalid mesh handle");
    Object o;
    o.mesh = mesh;
    o.color = to_glm(color);
    Handle h = next_object_++;
    objects_[h] = o;
    return h;
}

void Renderer::destroy_object(Handle obj) { objects_.erase(obj); }

void Renderer::set_transform(Handle obj, Vec3 pos, Vec3 rot_deg, Vec3 scale) {
    Object& o = objects_.at(obj);
    o.pos = to_glm(pos);
    o.rot = to_glm(rot_deg);
    o.scale = to_glm(scale);
}

void Renderer::set_color(Handle obj, Vec3 color) { objects_.at(obj).color = to_glm(color); }
void Renderer::set_visible(Handle obj, bool visible) { objects_.at(obj).visible = visible; }

void Renderer::set_camera(Vec3 pos, float yaw_deg, float pitch_deg) {
    float y = glm::radians(yaw_deg), p = glm::radians(pitch_deg);
    cam_pos_ = to_glm(pos);
    // yaw 0 looks down -Z, positive yaw turns right (+X)
    cam_fwd_ = glm::normalize(glm::vec3(std::sin(y) * std::cos(p), std::sin(p), -std::cos(y) * std::cos(p)));
}

void Renderer::set_flashlight(bool on) { flashlight_ = on; }
void Renderer::set_fog(Vec3 color, float density) { fog_color_ = to_glm(color); fog_density_ = density; }
void Renderer::set_ambient(Vec3 color) { ambient_ = to_glm(color); }

void Renderer::render(int ww, int wh) {
    // ---- pass 1: scene -> low-res framebuffer ----
    glBindFramebuffer(GL_FRAMEBUFFER, fbo_);
    glViewport(0, 0, low_w_, low_h_);
    glEnable(GL_DEPTH_TEST);
    glEnable(GL_CULL_FACE);
    glCullFace(GL_BACK);
    glClearColor(fog_color_.r, fog_color_.g, fog_color_.b, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);

    glm::mat4 view = glm::lookAt(cam_pos_, cam_pos_ + cam_fwd_, glm::vec3(0, 1, 0));
    glm::mat4 proj = glm::perspective(glm::radians(70.0f), float(low_w_) / float(low_h_), 0.05f, 100.0f);

    scene_->use();
    scene_->set("uView", view);
    scene_->set("uProj", proj);
    scene_->set("uRes", glm::vec2(float(low_w_), float(low_h_)));
    scene_->set("uCamPos", cam_pos_);
    scene_->set("uCamDir", cam_fwd_);
    scene_->set("uAmbient", ambient_);
    scene_->set("uFogColor", fog_color_);
    scene_->set("uFogDensity", fog_density_);
    scene_->set("uFlashlight", flashlight_ ? 1 : 0);

    for (const auto& [h, o] : objects_) {
        if (!o.visible) continue;
        glm::mat4 model(1.0f);
        model = glm::translate(model, o.pos);
        model = glm::rotate(model, glm::radians(o.rot.y), glm::vec3(0, 1, 0));
        model = glm::rotate(model, glm::radians(o.rot.x), glm::vec3(1, 0, 0));
        model = glm::rotate(model, glm::radians(o.rot.z), glm::vec3(0, 0, 1));
        model = glm::scale(model, o.scale);
        scene_->set("uModel", model);
        scene_->set("uColor", o.color);
        meshes_[o.mesh - 1]->draw();
    }

    // ---- pass 2: upscale to the window with nearest filtering + post effects ----
    glBindFramebuffer(GL_FRAMEBUFFER, 0);
    glDisable(GL_DEPTH_TEST);
    glDisable(GL_CULL_FACE);
    glViewport(0, 0, ww, wh);
    glClearColor(0.0f, 0.0f, 0.0f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);

    float scale = std::min(float(ww) / low_w_, float(wh) / low_h_);  // keep aspect, letterbox
    int vw = int(low_w_ * scale), vh = int(low_h_ * scale);
    glViewport((ww - vw) / 2, (wh - vh) / 2, vw, vh);

    post_->use();
    glActiveTexture(GL_TEXTURE0);
    glBindTexture(GL_TEXTURE_2D, color_tex_);
    post_->set("uTex", 0);
    post_->set("uRes", glm::vec2(float(low_w_), float(low_h_)));
    glBindVertexArray(empty_vao_);
    glDrawArrays(GL_TRIANGLES, 0, 3);
}
