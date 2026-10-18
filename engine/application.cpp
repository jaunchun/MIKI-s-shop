#include <GL/glew.h>
#include <GLFW/glfw3.h>
#include <stdexcept>
#include "application.h"

// internal render resolution: the low-poly / retro look comes from this
static constexpr int kLowW = 320;
static constexpr int kLowH = 240;

Application::Application(int width, int height, const std::string& title) {
    if (!glfwInit()) throw std::runtime_error("glfwInit failed");

    glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 3);
    glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 3);
    glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
#ifdef __APPLE__
    glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
#endif

    window_ = glfwCreateWindow(width, height, title.c_str(), nullptr, nullptr);
    if (!window_) {
        glfwTerminate();
        throw std::runtime_error("could not create window (OpenGL 3.3 required)");
    }
    glfwMakeContextCurrent(window_);
    glfwSwapInterval(1);

    glewExperimental = GL_TRUE;
    if (glewInit() != GLEW_OK) {
        glfwDestroyWindow(window_);
        glfwTerminate();
        throw std::runtime_error("glewInit failed");
    }
    glGetError();  // glewInit can leave a harmless GL error behind

    input_.attach(window_);
    renderer_ = std::make_unique<Renderer>(kLowW, kLowH);
    last_time_ = glfwGetTime();
}

Application::~Application() {
    renderer_.reset();  // free GL objects while the context still exists
    if (window_) glfwDestroyWindow(window_);
    glfwTerminate();
}

bool Application::running() const { return window_ && !glfwWindowShouldClose(window_); }

void Application::quit() { glfwSetWindowShouldClose(window_, GLFW_TRUE); }

double Application::begin_frame() {
    input_.update();     // must come BEFORE polling
    glfwPollEvents();
    double now = glfwGetTime();
    double dt = now - last_time_;
    last_time_ = now;
    if (dt > 0.1) dt = 0.1;  // avoid huge steps after a stall
    return dt;
}

void Application::end_frame() {
    int fw = 0, fh = 0;
    glfwGetFramebufferSize(window_, &fw, &fh);
    renderer_->render(fw, fh);
    glfwSwapBuffers(window_);
}
