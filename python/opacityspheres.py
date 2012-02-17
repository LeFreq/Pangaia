from visual import *
from random import *
from graph import *

#TODO
#set a fixed light at the top, and make a frame that will rotate objects without affecting the light.
#consider the vpython4 attenuation attribute of a light source and consider that it is a factor of the scaling relationship between the light source and the objects.

scene.title="opacity test"
scene.width, scene.height = 1440, 900
scene.lights=[ ]
#scene.lights=[local_light(pos=(0,0,0), color=color.green, local=True, attentuation=(1,1,5))]
#scene.lights=[distant_light(direction=(0, 1, 0), color=color.green, attentuation=(1,1,10))] #(1,1,0.8))]
scene.material=materials.emissive
scene.ambient=color.gray(0.05)
defcolor = (0,0.7,0.1)
defopacity = 0.8 #0.05
numspheres = 100
#scene.stereo="redcyan"

f=frame()

cities={"Denver","Seattle","Portland","Boise","Fargo","LA"}
#g=Graph()
#print(g)


def rand3tuple(start, stop):
    """"Return a 3-tuple  consiting of random integers between start and stop."""
    return (randint(start, stop), randint(start, stop), randint(start, stop*2))


#class mysphere(sphere):

#    def __init__(self, thickness=5, **kwargs):
#        super().__init__(**kwargs)
#        try:
#            radius=kwargs["radius"]
#            radius=max(1,radius-thickness)
#        except KeyError:
#            pass
#        kwargs["radius"]=radius
#        sphere(kwargs) #draw a second sphere


#This looks nice: inner sphere: chrome, light.color=green, outsphere=glass, opacity=0.4
#Also, inner sphere: glass, color=gray, opacity=0.5, outsphere, glass, color=green, opacity=0.3

def mysphere(pos, color, opacity, radius, thickness=10, **kwargs):
    sphere(pos=pos, color=(0.5,0.5,0.5) , opacity=0.5, material=materials.chrome, radius=max(1, radius-thickness), **kwargs) #inner sphere
    POS2=vector(pos)+vector(0,1,0)
    if randint(1,50) == 10:
        print("lit")
        local_light(pos=pos, color=(0,0.7,0))
        sphere(pos=pos, radius=10, color=(0,1,0), materials=materials.emissive)
    sphere(pos=pos, color=(0,1,0.5), opacity=0.1, radius=radius, material=materials.glass, **kwargs)


#local_light(pos=(0,0,0))
#sphere(radius=10,pos=(0,0,0), materials=materials.chrome)
for i in range(numspheres):
    mysphere(pos=rand3tuple(-5000,5000), color=defcolor, opacity=defopacity, radius=randint(1,500))

nodes = scene.objects[:]
for s in nodes:
    tail=choice(nodes) #pick a random destination node
    #cylinder(pos=s.pos, axis=tail.pos, radius=10, color=(0.1,0.1,0.1))
    #curve(pos=[s.pos, tail.pos], color=(0.5,0.5,0.5), radius=4)

#for i in arange(0,pi):
#    f.axis=(0,i,0)

while True:
    rate(100)
    #f=scene.forward
    #print(scene.forward)
    if scene.mouse.events:
        mm=scene.mouse.getevent()
        if mm.pick==None: #create new sphere
            pass #g[mysphere(pos=mm.pos,radius=1)]
        else:
            print(mm.pick, mm.pick.radius)
            if mm.shift:
                mm.pick.radius+=1
            else:
                mm.pick.radius-=1
    
#Experiment with crude fog
#size_units="world"
#l=[]
#for i in range(1000000):
#    l.append(rand3tuple(-5000,5000))    
#points(pos=l, size=2, color=color.gray(0.5), size_units="world")

#sphere(frame=f, pos=(0,10,0), color=color.white, opacity=0.5, radius=1)
#sphere(color=color.gray(0.5), opacity=0.5, radius=2)
#sphere(frame=f, pos=(0,10,1), color=color.yellow, opacity=0.5, radius=4)


#sphere(color=color.green, opacity=0.1, radius=6)
#s=sphere(color=color.green, opacity=0.1, radius=8)
#sphere(color=color.green, opacity=0.1, radius=10)

#while not scene.kb.keys:
#    for i in arange(0,10,0.1): #uses numpy for float ranges
#        rate(10)
 #       s.opacity=i/10
 #   for i in arange(10,0,-0.1):
 #       rate(10)
 #       s.opacity=i/10
