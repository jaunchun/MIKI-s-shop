#include <GLFW/glfw3.h>
#include "input.h"

void Input::attach(GLFWwindow* window) {
    window_ = window;
    glfwSetWindowUserPointer(window, this);
    glfwSetKeyCallback(window, key_cb);
    glfwSetMouseButtonCallback(window, mouse_btn_cb);
    glfwSetCursorPosCallback(window, cursor_cb);
    glfwSetScrollCallback(window, scroll_cb);
}

void Input::update() {
    prev_keys_ = keys_;
    prev_buttons_ = buttons_;
    dx_ = dy_ = 0;   // callbacks refill these during glfwPollEvents
    scroll_ = 0;
}

bool Input::key_down(int k) const     { return k >= 0 && k < MAX_KEYS && keys_[k]; }
bool Input::key_pressed(int k) const  { return k >= 0 && k < MAX_KEYS && keys_[k] && !prev_keys_[k]; }
bool Input::key_released(int k) const { return k >= 0 && k < MAX_KEYS && !keys_[k] && prev_keys_[k]; }

bool Input::mouse_down(int b) const    { return b >= 0 && b < MAX_BUTTONS && buttons_[b]; }
bool Input::mouse_pressed(int b) const { return b >= 0 && b < MAX_BUTTONS && buttons_[b] && !prev_buttons_[b]; }

std::pair<double, double> Input::mouse_pos() const   { return {mx_, my_}; }
std::pair<double, double> Input::mouse_delta() const { return {dx_, dy_}; }
double Input::scroll() const { return scroll_; }

void Input::set_cursor_locked(bool locked) {
    locked_ = locked;
    glfwSetInputMode(window_, GLFW_CURSOR, locked ? GLFW_CURSOR_DISABLED : GLFW_CURSOR_NORMAL);
    if (glfwRawMouseMotionSupported())
        glfwSetInputMode(window_, GLFW_RAW_MOUSE_MOTION, locked ? GLFW_TRUE : GLFW_FALSE);
    first_mouse_ = true;   // avoid a big jump on the next move
}

void Input::key_cb(GLFWwindow* w, int key, int, int action, int) {
    auto* in = static_cast<Input*>(glfwGetWindowUserPointer(w));
    if (key < 0 || key >= MAX_KEYS) return;
    if (action == GLFW_PRESS)        in->keys_[key] = true;
    else if (action == GLFW_RELEASE) in->keys_[key] = false;   // ignore GLFW_REPEAT
}

void Input::mouse_btn_cb(GLFWwindow* w, int button, int action, int) {
    auto* in = static_cast<Input*>(glfwGetWindowUserPointer(w));
    if (button < 0 || button >= MAX_BUTTONS) return;
    if (action == GLFW_PRESS)        in->buttons_[button] = true;
    else if (action == GLFW_RELEASE) in->buttons_[button] = false;
}

void Input::cursor_cb(GLFWwindow* w, double x, double y) {
    auto* in = static_cast<Input*>(glfwGetWindowUserPointer(w));
    if (in->first_mouse_) { in->mx_ = x; in->my_ = y; in->first_mouse_ = false; }
    in->dx_ += x - in->mx_;
    in->dy_ += y - in->my_;
    in->mx_ = x;
    in->my_ = y;
}

void Input::scroll_cb(GLFWwindow* w, double, double yoff) {
    static_cast<Input*>(glfwGetWindowUserPointer(w))->scroll_ += yoff;
}
