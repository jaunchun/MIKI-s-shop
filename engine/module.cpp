#include <pybind11/pybind11.h>
#include <pybind11/stl.h>   // tuple/list <-> std::array / std::pair
#include <GLFW/glfw3.h>
#include "application.h"

namespace py = pybind11;

PYBIND11_MODULE(engine, m) {
    m.doc() = "Detention engine (C++ renderer, input, window)";

    py::class_<Input>(m, "Input")
        .def("key_down",        &Input::key_down)
        .def("key_pressed",     &Input::key_pressed)
        .def("key_released",    &Input::key_released)
        .def("mouse_down",      &Input::mouse_down)
        .def("mouse_pressed",   &Input::mouse_pressed)
        .def("mouse_pos",       &Input::mouse_pos)
        .def("mouse_delta",     &Input::mouse_delta)
        .def("scroll",          &Input::scroll)
        .def("set_cursor_locked", &Input::set_cursor_locked)
        .def_property_readonly("cursor_locked", &Input::cursor_locked);

    py::class_<Renderer>(m, "Renderer")
        .def("load_mesh",      &Renderer::load_mesh, py::arg("name_or_path"))
        .def("create_object",  &Renderer::create_object,
             py::arg("mesh"), py::arg("color") = Vec3{0.7f, 0.7f, 0.7f})
        .def("destroy_object", &Renderer::destroy_object)
        .def("set_transform",  &Renderer::set_transform,
             py::arg("obj"), py::arg("pos"), py::arg("rot"), py::arg("scale"))
        .def("set_color",      &Renderer::set_color)
        .def("set_visible",    &Renderer::set_visible)
        .def("set_camera",     &Renderer::set_camera,
             py::arg("pos"), py::arg("yaw"), py::arg("pitch"))
        .def("set_flashlight", &Renderer::set_flashlight)
        .def("set_fog",        &Renderer::set_fog, py::arg("color"), py::arg("density"))
        .def("set_ambient",    &Renderer::set_ambient);

    py::class_<Application>(m, "Application")
        .def(py::init<int, int, std::string>(),
             py::arg("width"), py::arg("height"), py::arg("title"))
        .def("running",     &Application::running)
        .def("quit",        &Application::quit)
        .def("begin_frame", &Application::begin_frame)
        .def("end_frame",   &Application::end_frame)
        .def_property_readonly("input", &Application::input,
                               py::return_value_policy::reference_internal)
        .def_property_readonly("renderer", &Application::renderer,
                               py::return_value_policy::reference_internal);

    // ---- keys ----
    m.attr("KEY_W")     = GLFW_KEY_W;
    m.attr("KEY_A")     = GLFW_KEY_A;
    m.attr("KEY_S")     = GLFW_KEY_S;
    m.attr("KEY_D")     = GLFW_KEY_D;
    m.attr("KEY_E")     = GLFW_KEY_E;
    m.attr("KEY_F")     = GLFW_KEY_F;
    m.attr("KEY_TAB")   = GLFW_KEY_TAB;
    m.attr("KEY_CTRL")  = GLFW_KEY_LEFT_CONTROL;
    m.attr("KEY_SPACE") = GLFW_KEY_SPACE;
    m.attr("KEY_SHIFT") = GLFW_KEY_LEFT_SHIFT;
    m.attr("KEY_ESC")   = GLFW_KEY_ESCAPE;
    m.attr("KEY_1")     = GLFW_KEY_1;
    m.attr("KEY_2")     = GLFW_KEY_2;
    m.attr("KEY_3")     = GLFW_KEY_3;
    m.attr("KEY_4")     = GLFW_KEY_4;

    // ---- mouse ----
    m.attr("M_LEFT")  = GLFW_MOUSE_BUTTON_LEFT;
    m.attr("M_RIGHT") = GLFW_MOUSE_BUTTON_RIGHT;
}
