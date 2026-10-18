#pragma once
#include <array>
#include <utility>

struct GLFWwindow;

class Input {
public:
    void attach(GLFWwindow* window);   // once, after creating the window
    void update();                     // once per frame, BEFORE glfwPollEvents

    bool key_down(int key) const;      // held
    bool key_pressed(int key) const;   // went down this frame
    bool key_released(int key) const;  // went up this frame

    bool mouse_down(int button) const;
    bool mouse_pressed(int button) const;
    std::pair<double, double> mouse_pos() const;
    std::pair<double, double> mouse_delta() const;  // since last frame
    double scroll() const;                          // wheel since last frame

    void set_cursor_locked(bool locked);
    bool cursor_locked() const { return locked_; }

private:
    static constexpr int MAX_KEYS = 350;
    static constexpr int MAX_BUTTONS = 8;

    GLFWwindow* window_ = nullptr;
    std::array<bool, MAX_KEYS> keys_{}, prev_keys_{};
    std::array<bool, MAX_BUTTONS> buttons_{}, prev_buttons_{};
    double mx_ = 0, my_ = 0, dx_ = 0, dy_ = 0, scroll_ = 0;
    bool first_mouse_ = true;
    bool locked_ = false;

    static void key_cb(GLFWwindow*, int key, int, int action, int);
    static void mouse_btn_cb(GLFWwindow*, int button, int action, int);
    static void cursor_cb(GLFWwindow*, double x, double y);
    static void scroll_cb(GLFWwindow*, double, double yoff);
};
