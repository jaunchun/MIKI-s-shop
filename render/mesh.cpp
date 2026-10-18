#include <GL/glew.h>
#include <cstddef>
#include <fstream>
#include <sstream>
#include <stdexcept>
#include "mesh.h"

Mesh::Mesh(const std::vector<Vertex>& v) : count_(static_cast<int>(v.size())) {
    glGenVertexArrays(1, &vao_);
    glGenBuffers(1, &vbo_);
    glBindVertexArray(vao_);
    glBindBuffer(GL_ARRAY_BUFFER, vbo_);
    glBufferData(GL_ARRAY_BUFFER, v.size() * sizeof(Vertex), v.data(), GL_STATIC_DRAW);
    glEnableVertexAttribArray(0);
    glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex),
                          reinterpret_cast<void*>(offsetof(Vertex, pos)));
    glEnableVertexAttribArray(1);
    glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, sizeof(Vertex),
                          reinterpret_cast<void*>(offsetof(Vertex, normal)));
    glBindVertexArray(0);
}

Mesh::~Mesh() {
    if (vbo_) glDeleteBuffers(1, &vbo_);
    if (vao_) glDeleteVertexArrays(1, &vao_);
}

void Mesh::draw() const {
    glBindVertexArray(vao_);
    glDrawArrays(GL_TRIANGLES, 0, count_);
}

static void add_quad(std::vector<Vertex>& v, glm::vec3 a, glm::vec3 b, glm::vec3 c, glm::vec3 d, glm::vec3 n) {
    v.push_back({a, n}); v.push_back({b, n}); v.push_back({c, n});
    v.push_back({a, n}); v.push_back({c, n}); v.push_back({d, n});
}

std::unique_ptr<Mesh> Mesh::cube() {
    const float h = 0.5f;
    std::vector<Vertex> v;
    add_quad(v, {-h,-h, h}, { h,-h, h}, { h, h, h}, {-h, h, h}, { 0, 0, 1});  // +Z
    add_quad(v, { h,-h,-h}, {-h,-h,-h}, {-h, h,-h}, { h, h,-h}, { 0, 0,-1});  // -Z
    add_quad(v, { h,-h, h}, { h,-h,-h}, { h, h,-h}, { h, h, h}, { 1, 0, 0});  // +X
    add_quad(v, {-h,-h,-h}, {-h,-h, h}, {-h, h, h}, {-h, h,-h}, {-1, 0, 0});  // -X
    add_quad(v, {-h, h, h}, { h, h, h}, { h, h,-h}, {-h, h,-h}, { 0, 1, 0});  // +Y
    add_quad(v, {-h,-h,-h}, { h,-h,-h}, { h,-h, h}, {-h,-h, h}, { 0,-1, 0});  // -Y
    return std::make_unique<Mesh>(v);
}

std::unique_ptr<Mesh> Mesh::plane() {
    const float h = 0.5f;
    std::vector<Vertex> v;
    add_quad(v, {-h, 0, h}, { h, 0, h}, { h, 0,-h}, {-h, 0,-h}, {0, 1, 0});
    return std::make_unique<Mesh>(v);
}

std::unique_ptr<Mesh> Mesh::from_obj(const std::string& path) {
    std::ifstream f(path);
    if (!f) throw std::runtime_error("cannot open mesh: " + path);

    std::vector<glm::vec3> pos;
    std::vector<Vertex> out;
    std::string line;
    while (std::getline(f, line)) {
        std::istringstream ss(line);
        std::string tag;
        ss >> tag;
        if (tag == "v") {
            glm::vec3 p;
            ss >> p.x >> p.y >> p.z;
            pos.push_back(p);
        } else if (tag == "f") {
            std::vector<int> idx;
            std::string tok;
            while (ss >> tok) {
                int i = std::stoi(tok.substr(0, tok.find('/')));
                idx.push_back(i < 0 ? static_cast<int>(pos.size()) + i : i - 1);
            }
            for (size_t k = 1; k + 1 < idx.size(); ++k) {  // fan-triangulate
                glm::vec3 a = pos.at(idx[0]), b = pos.at(idx[k]), c = pos.at(idx[k + 1]);
                glm::vec3 n = glm::cross(b - a, c - a);
                float len = glm::length(n);
                n = len > 1e-8f ? n / len : glm::vec3(0, 1, 0);   // flat shading
                out.push_back({a, n}); out.push_back({b, n}); out.push_back({c, n});
            }
        }
    }
    if (out.empty()) throw std::runtime_error("mesh has no faces: " + path);
    return std::make_unique<Mesh>(out);
}
