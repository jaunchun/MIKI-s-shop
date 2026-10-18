#pragma once
#include <array>
#include <cstdint>
#include <memory>
#include <string>
#include <unordered_map>
#include <vector>
#include <glm/glm.hpp>
#include "mesh.h"
#include "shader.h"

using Vec3 = std::array<float, 3>;
using Handle = std::uint32_t;

class Renderer {
public:
    Renderer(int low_w, int low_h);
    ~Renderer();
    Renderer(const Renderer&) = delete;
    Renderer& operator=(const Renderer&) = delete;

    // meshes: "cube", "plane" or a path to an .obj file (cached)
    Handle load_mesh(const std::string& name_or_path);

    Handle create_object(Handle mesh, Vec3 color);
    void destroy_object(Handle obj);
    void set_transform(Handle obj, Vec3 pos, Vec3 rot_deg, Vec3 scale);
    void set_color(Handle obj, Vec3 color);
    void set_visible(Handle obj, bool visible);

    void set_camera(Vec3 pos, float yaw_deg, float pitch_deg);
    void set_flashlight(bool on);
    void set_fog(Vec3 color, float density);
    void set_ambient(Vec3 color);

    void render(int window_w, int window_h);

private:
    struct Object {
        Handle mesh = 0;
        glm::vec3 pos{0.0f}, rot{0.0f}, scale{1.0f}, color{0.7f};
        bool visible = true;
    };

    int low_w_, low_h_;
    unsigned int fbo_ = 0, color_tex_ = 0, depth_rb_ = 0, empty_vao_ = 0;
    std::unique_ptr<Shader> scene_, post_;

    std::vector<std::unique_ptr<Mesh>> meshes_;           // handle = index + 1
    std::unordered_map<std::string, Handle> mesh_cache_;
    std::unordered_map<Handle, Object> objects_;
    Handle next_object_ = 1;

    glm::vec3 cam_pos_{0.0f, 1.6f, 0.0f};
    glm::vec3 cam_fwd_{0.0f, 0.0f, -1.0f};
    glm::vec3 fog_color_{0.02f, 0.02f, 0.03f};
    glm::vec3 ambient_{0.10f, 0.10f, 0.13f};
    float fog_density_ = 0.12f;
    bool flashlight_ = true;
};
