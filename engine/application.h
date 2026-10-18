#pragma once
#include <memory>
#include <string>
#include "input/input.h"
#include "render/renderer.h"

struct GLFWwindow;

class Application {
public:
    Application(int width, int height, const std::string& title);
    ~Application();
    Application(const Application&) = delete;
    Application& operator=(const Application&) = delete;

    bool running() const;
    void quit();
    double begin_frame();   // polls input, returns delta time (seconds)
    void end_frame();       // renders the scene and swaps buffers

    Input& input() { return input_; }
    Renderer& renderer() { return *renderer_; }

private:
    GLFWwindow* window_ = nullptr;
    Input input_;
    std::unique_ptr<Renderer> renderer_;
    double last_time_ = 0.0;
};
