using Plots, ImageView, Images

anim = @animate for i = 0 : 26
    imga = load("microsystem.png")
    imgb = load("pressure.png")
    imgc = load("grains.png")
    imgd = load("velocity.png")
    imge = load("mesh.png")
    imgf = load("$i.png")
    axis = ([], false)
    p1 = plot(imga, axis = nothing, border=:none, titlefontsize = 40, title = "a) Input image" )
    p2 = plot(imgb, axis = nothing, border=:none, titlefontsize = 40, title = "d) Simulated pressure")
    p3 = plot(imgc, axis = nothing, border=:none, titlefontsize = 40, title = "b) Extracted contours")
    p4 = plot(imgd, axis = nothing, border=:none, titlefontsize = 40, title = "e) Simulated velocity")
    p5 = plot(imge, axis = nothing, border=:none, titlefontsize = 40, title = "c) Generated mesh")
    p6 = plot(imgf, axis = nothing, border=:none, titlefontsize = 40, title = "f) Simulated tracer")
    plot(p1, p2, p3, p4, p5, p6, layout = (3, 2), axis = nothing, border=:none, size = (4500, 2700))
end

gif(anim, "pymm.gif", fps = 1)
