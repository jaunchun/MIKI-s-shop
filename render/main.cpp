#include <windows.h>
#include <GL/gl.h>

#include <cstdlib>

namespace
{
    HDC deviceContext = nullptr;

    void Render(HWND window)
    {
        RECT clientRect{};
        GetClientRect(window, &clientRect);

        const int width = clientRect.right - clientRect.left;
        const int height = clientRect.bottom - clientRect.top;
        if (width <= 0 || height <= 0)
        {
            return;
        }

        glViewport(0, 0, width, height);
        glClearColor(0.08f, 0.09f, 0.14f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        glMatrixMode(GL_PROJECTION);
        glLoadIdentity();
        glMatrixMode(GL_MODELVIEW);
        glLoadIdentity();
        glShadeModel(GL_SMOOTH);

        glBegin(GL_TRIANGLES);
        glColor3f(1.0f, 0.25f, 0.35f);
        glVertex2f(0.0f, 0.75f);

        glColor3f(0.2f, 0.85f, 1.0f);
        glVertex2f(-0.7f, -0.6f);

        glColor3f(0.65f, 0.3f, 1.0f);
        glVertex2f(0.7f, -0.6f);
        glEnd();

        SwapBuffers(deviceContext);
    }

    LRESULT CALLBACK WindowProcedure(HWND window, UINT message, WPARAM wParam, LPARAM lParam)
    {
        switch (message)
        {
        case WM_PAINT:
        {
            PAINTSTRUCT paint{};
            BeginPaint(window, &paint);
            Render(window);
            EndPaint(window, &paint);
            return 0;
        }
        case WM_SIZE:
            InvalidateRect(window, nullptr, FALSE);
            return 0;
        case WM_ERASEBKGND:
            return 1;
        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
        default:
            return DefWindowProc(window, message, wParam, lParam);
        }
    }

    void ShowError(const char* message)
    {
        MessageBoxA(nullptr, message, "OpenGL triangle", MB_OK | MB_ICONERROR);
    }
}

int main()
{
    HINSTANCE instance = GetModuleHandle(nullptr);
    const char* className = "GradientTriangleWindow";

    WNDCLASSA windowClass{};
    windowClass.style = CS_OWNDC;
    windowClass.lpfnWndProc = WindowProcedure;
    windowClass.hInstance = instance;
    windowClass.hCursor = LoadCursor(nullptr, IDC_ARROW);
    windowClass.lpszClassName = className;

    if (!RegisterClassA(&windowClass))
    {
        ShowError("Could not register the window class.");
        return EXIT_FAILURE;
    }

    RECT bounds{ 0, 0, 960, 640 };
    AdjustWindowRect(&bounds, WS_OVERLAPPEDWINDOW, FALSE);
    HWND window = CreateWindowA(
        className,
        "OpenGL Gradient Triangle",
        WS_OVERLAPPEDWINDOW,
        CW_USEDEFAULT,
        CW_USEDEFAULT,
        bounds.right - bounds.left,
        bounds.bottom - bounds.top,
        nullptr,
        nullptr,
        instance,
        nullptr);

    if (!window)
    {
        ShowError("Could not create the window.");
        UnregisterClassA(className, instance);
        return EXIT_FAILURE;
    }

    deviceContext = GetDC(window);
    if (!deviceContext)
    {
        ShowError("Could not get the window's device context.");
        DestroyWindow(window);
        UnregisterClassA(className, instance);
        return EXIT_FAILURE;
    }

    PIXELFORMATDESCRIPTOR pixelFormat{};
    pixelFormat.nSize = sizeof(pixelFormat);
    pixelFormat.nVersion = 1;
    pixelFormat.dwFlags = PFD_DRAW_TO_WINDOW | PFD_SUPPORT_OPENGL | PFD_DOUBLEBUFFER;
    pixelFormat.iPixelType = PFD_TYPE_RGBA;
    pixelFormat.cColorBits = 32;
    pixelFormat.iLayerType = PFD_MAIN_PLANE;

    const int format = ChoosePixelFormat(deviceContext, &pixelFormat);
    if (format == 0 || !SetPixelFormat(deviceContext, format, &pixelFormat))
    {
        ShowError("Could not set the OpenGL pixel format.");
        ReleaseDC(window, deviceContext);
        DestroyWindow(window);
        UnregisterClassA(className, instance);
        return EXIT_FAILURE;
    }

    HGLRC renderContext = wglCreateContext(deviceContext);
    if (!renderContext || !wglMakeCurrent(deviceContext, renderContext))
    {
        ShowError("Could not create the OpenGL rendering context.");
        if (renderContext)
        {
            wglDeleteContext(renderContext);
        }
        ReleaseDC(window, deviceContext);
        DestroyWindow(window);
        UnregisterClassA(className, instance);
        return EXIT_FAILURE;
    }

    ShowWindow(window, SW_SHOW);
    UpdateWindow(window);

    MSG message{};
    while (GetMessage(&message, nullptr, 0, 0) > 0)
    {
        TranslateMessage(&message);
        DispatchMessage(&message);
    }

    wglMakeCurrent(nullptr, nullptr);
    wglDeleteContext(renderContext);
    ReleaseDC(window, deviceContext);
    UnregisterClassA(className, instance);
    return static_cast<int>(message.wParam);
}