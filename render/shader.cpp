#include <GL/glew.h>
#include <glm/gtc/type_ptr.hpp>
#include <stdexcept>
#include <string>
#include "shader.h"

static unsigned int compile(unsigned int type, const char* src) {
    unsigned int s = glCreateShader(type);
    glShaderSource(s, 1, &src, nullptr);
    glCompileShader(s);
    int ok = 0;
    glGetShaderiv(s, GL_COMPILE_STATUS, &ok);
    if (!ok) {
        char log[2048];
        glGetShaderInfoLog(s, sizeof(log), nullptr, log);
        glDeleteShader(s);
        throw std::runtime_error(std::string("shader compile error:\n") + log);
    }
    return s;
}

Shader::Shader(const char* vertex_src, const char* fragment_src) {
    unsigned int vs = compile(GL_VERTEX_SHADER, vertex_src);
    unsigned int fs = compile(GL_FRAGMENT_SHADER, fragment_src);
    id_ = glCreateProgram();
    glAttachShader(id_, vs);
    glAttachShader(id_, fs);
    glLinkProgram(id_);
    glDeleteShader(vs);
    glDeleteShader(fs);
    int ok = 0;
    glGetProgramiv(id_, GL_LINK_STATUS, &ok);
    if (!ok) {
        char log[2048];
        glGetProgramInfoLog(id_, sizeof(log), nullptr, log);
        throw std::runtime_error(std::string("shader link error:\n") + log);
    }
}

Shader::~Shader() { if (id_) glDeleteProgram(id_); }

void Shader::use() const { glUseProgram(id_); }
int Shader::loc(const char* n) const { return glGetUniformLocation(id_, n); }

void Shader::set(const char* n, int v) const   { glUniform1i(loc(n), v); }
void Shader::set(const char* n, float v) const { glUniform1f(loc(n), v); }
void Shader::set(const char* n, const glm::vec2& v) const { glUniform2fv(loc(n), 1, glm::value_ptr(v)); }
void Shader::set(const char* n, const glm::vec3& v) const { glUniform3fv(loc(n), 1, glm::value_ptr(v)); }
void Shader::set(const char* n, const glm::mat4& v) const { glUniformMatrix4fv(loc(n), 1, GL_FALSE, glm::value_ptr(v)); }
