from glumpy import app, gloo, gl

window = app.Window()

vertex = """
         attribute vec2 position;
         void main()
         {
             gl_Position = vec4(position, 0.0, 1.0);
         } """

fragment = """
           uniform vec4 color;
           void main() {
               gl_FragColor = color;
           } """

quad = gloo.Program(vertex, fragment, count=4)

quad['position'] = [(-0.5, -0.5),
                    (-0.5, +0.5),
                    (+0.5, -0.5),
                    (+0.5, +0.5)]
quad['color'] = 1,0,0,1  # red

# @window.event
# def on_draw(dt):
#     window.clear()
#     quad.draw(gl.GL_TRIANGLE_STRIP)

# app.run()


vertex = """
         uniform float time;
         attribute vec2 position;
         void main()
         {
             vec2 xy = vec2(sin(2.0*time));
             gl_Position = vec4(position*(0.25 + 0.75*xy*xy), 0.0, 1.0);
         } """

quad = gloo.Program(vertex, fragment, count=4)


@window.event
def on_draw(dt):
    window.clear()
    quad["time"] += dt
    quad.draw(gl.GL_TRIANGLE_STRIP)

quad["time"] = 0.0
quad['color'] = 1,0,0,1
quad['position'] = [(-1, -1), (-1, +1), (+1, -1), (+1, +1)]
app.run()
