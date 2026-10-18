#pragma once
#include <glm/glm.hpp>

class Shader {
public:
    Shader(const char* vertex_src, const char* fragment_src);
    ~Shader();
    Shader(const Shader&) = delete;
    Shader& operator=(const Shader&) = delete;

    void use() const;
    void set(const char* name, int v) const;
    void set(const char* name, float v) const;
    void set(const char* name, const glm::vec2& v) const;
    void set(const char* name, const glm::vec3& v) const;
    void set(const char* name, const glm::mat4& v) const;

private:
    unsigned int id_ = 0;
    int loc(const char* name) const;
};
