from visual import *
from random import *
from graph import *

#TODO
#set a fixed light at the top, and make a frame that will rotate objects without affecting the light.
#consider the vpython4 attenuation attribute of a light source and consider that it is a factor of the scaling relationship between the light source and the objects.
#Also, using the built-in camera with eye-tracking for depth discernment (courtesy Geoff Chesshire)

scene.title="opacity test"
scene.width, scene.height = 1440, 900
worldradius = 5000
#scene.lights=[ ]
scene.lights=[local_light(pos=(0,0,0), color=color.green, local=True, attentuation=(1,1,5))]
#scene.lights=[distant_light(direction=(0, 1, 0), color=color.green, attentuation=(1,1,10))] #(1,1,0.8))]
scene.material=materials.emissive
scene.ambient=color.gray(0.05)
defcolor = (0,0.7,0.1)
defopacity = 0.8 #0.05
numspheres = 100
#scene.stereo="redcyan"


## Should encapsulate these into a class, integrated with graph nodes.
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


def rand3tuple(start= -worldradius, stop = worldradius):
    """"Return a 3-tuple  consiting of random integers between start and stop."""
    return (randint(start, stop), randint(start, stop), randint(start, stop*2))


#This looks nice: inner sphere: chrome, light.color=green, outsphere=glass, opacity=0.4
#Also, inner sphere: glass, color=gray, opacity=0.5, outsphere, glass, color=green, opacity=0.3
#, material=materials.solid

# Function for standardizing sphere drawing
def mysphere(pos, color, opacity, radius, thickness=10, **kwargs):
    sphere(pos=pos, color=(0,1,0) , opacity=1.0, radius=max(1, radius-thickness), **kwargs) #inner sphere
    POS2=vector(pos)+vector(0,1,0)
    if randint(1,50) == 10:
        print("lit")
        #local_light(pos=pos, color=(0,0.7,0))
        #sphere(pos=pos, radius=10, color=(0,1,0), materials=materials.emissive)
    sphere(pos=pos, color=(0,1,0.5), opacity=0.1, radius=radius, material=materials.glass, **kwargs)

## The actual drawing of spheres here
#local_light(pos=(0,0,0))
#sphere(radius=10,pos=(0,0,0), materials=materials.chrome)
for i in range(numspheres):
    mysphere(pos=rand3tuple(), color=defcolor, opacity=defopacity, radius=randint(1,0.1*worldradius))

### Experiment in edge drawing
##nodes = scene.objects[:]
##for s in nodes:
##    tail=choice(nodes) #pick a random destination node
##    cylinder(pos=s.pos, axis=tail.pos, radius=10, color=(0.1,0.1,0.1))
##    curve(pos=[s.pos, tail.pos], color=(0.5,0.5,0.5), radius=4)

### Rotation should be tried...
##for i in arange(0,pi):
##    f.axis=(0,i,0)

##Experiment with crude fog
#size_units="world"
#l=[]
#for i in range(1000000):
#    l.append(rand3tuple())    
#points(pos=l, size=1, color=color.gray(0.1), size_units="world")

# Simple event handling, currently only can click nodes and affect radius
while True:
    break
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
    

#cities={"Denver","Seattle","Portland","Boise","Fargo","LA"}
#g=Graph()
#print(g)
