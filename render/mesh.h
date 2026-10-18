#pragma once
#include <glm/glm.hpp>
#include <memory>
#include <string>
#include <vector>

struct Vertex {
    glm::vec3 pos;
    glm::vec3 normal;
};

class Mesh {
public:
    explicit Mesh(const std::vector<Vertex>& vertices);
    ~Mesh();
    Mesh(const Mesh&) = delete;
    Mesh& operator=(const Mesh&) = delete;

    void draw() const;

    static std::unique_ptr<Mesh> cube();   // unit cube, centred on origin
    static std::unique_ptr<Mesh> plane();  // 1x1 quad on XZ, facing +Y
    static std::unique_ptr<Mesh> from_obj(const std::string& path);  // v + f only

private:
    unsigned int vao_ = 0, vbo_ = 0;
    int count_ = 0;
};
