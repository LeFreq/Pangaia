#dreamingforward@gmail.com
#pangaia.sf.net

"""
A very crude demo giving a feel for the 3-d environment potential for a content-centric web.
Rotate view with the right-mouse drag and Zoom using both buttons (Mac: use Option key).
"""

#TODO:
#1) Add ability to Label a node.
#2) Add ability to Link/associate nodes.  Animate linking with some [[gravity model]], function of node mass, etc.
#3) Add ability to select a number of nodes and Group them.
#4) Currently drawing random nodes.  Create an interface to import gmail messages and prompt user to sort.
#5) since vpython has no depth shading, use built-in camera w/eye tracking to move the scene around as head moves.

#set a fixed light at the top, and make a frame that will rotate objects without affecting the light.
#consider the vpython4 attenuation attribute of a light source and consider that it is a factor of the scaling relationship between the light source and the objects.
#Also, using the built-in camera with eye-tracking for depth discernment (idea from Geoff Chesshire)

from __future__ import division   #XXX: shouldn't have to do this -- isn't it the future already?

from visual import *  #this pulls in the visual python library from the VPython
from random import *  #from the Python standard library
from graph import *   #pangaia module

#Rule of Thumb #1:  Put the most arbitrary values at the top of the code.  Let users tweak.
num_nodes = 100                     #number of spheres to draw
p_nodes_lit = 0.1                  #light 10% of the nodes

UserNodeName = "Neophyte"  #This will be your personal Node name as seen from the view of the social garden
default_name = "Node"      #Nodes will take this name plus a number

#visual constants
scene.width, scene.height = 1440, 900  #XXX change this to fit your screen, pixels.
scene.title = UserNodeName or raw_input("Name:") #prompt for user's name if not registered, "think for the future: what name do you want to be addressed as in eternity?"
#scene.lights=[ ]                  ##eliminate default lights
#scene.lights=local_light(pos=(0,0,0), color=color.white, local=True, attentuation=(1,1,5))
#scene.lights=[distant_light(direction=(0, 1, 0), color=color.white, attentuation=(1,1,10))] #(1,1,0.8))]
scene.material=materials.diffuse   #sets default material when none specifid
scene.ambient=color.gray(0.00)     #sets background light
#scene.stereo="redcyan"            #gives nice depth effect if you have red/cyan glasses, ultimately should use built-in camera if availble

world_radius = 5000                #this sets the default "size" of the world (as a starting point) as a reference for all vector ops.  XXX Should make a function of num_spheres, as radius=1 places a known lower bound.
base_color = color.green           #nodes start in the middle of the rainbow
base_opacity = 0.95                #A function of how much trust there is in the network.  Lower values ==> greater trust
default_mass = world_radius / 20   #specifies ratio of node radius to world radius

##The view in the blank window will depend on whether you're in your own Node (the "polar coordinate view) or viewing from outside it (the "cartesian veiw").
##Inside your node, you are seeing all the relationships that pertain to you, organized around your central basis (i.e. machine name)
##Outside your node, you navigate the (relatively unrelated) universe of nodes.
##Perhaps could zoom to edge of node-field and then (*bleep*) transit out to see the universe.


## Should encapsulate these into a class, integrated with graph nodes.
#class node(sphere):
#    def __init__(self, pos, mass, valence, lit, noosphere, **kwargs):
#        super().__init__(**kwargs)
#        try:
#            radius=kwargs["radius"]
#            radius=max(1,radius-thickness)
#        except KeyError:
#            pass
#        kwargs["radius"]=radius
#        sphere(kwargs) #draw a second sphere


def rand3tuple(start = -world_radius, stop = world_radius):
    """"Return a 3-tuple  consiting of random integers between start and stop."""
    return (randint(start, stop), randint(start, stop), randint(start, stop*2)) #note adjustment on z 


def atmos(valence, ambient=scene.ambient):   #XXX sloppy
    """Returns the color of the outershell, given node color and ambient background."""
    c = vector(color.rgb_to_hsv(vector(valence)*0.4))  #first reduce all color values
    #c[1] *= 0.5 #then, reduce saturation towards the background XXX:currently assuming ambient=gray of some kind
    c=vector(color.hsv_to_rgb(c))
    c[2] = min(c[2] + 0.2, 1)  #XXX this is totally arbitrary, but I like a little blue in there.  Ideally should move towards the ambient background color.
    return c

##def world_to_pixels(z):
##    """Adjust size for depth."""
##    return 1 + (world_radius * 2) / 20

#This looks nice: inner sphere: chrome, light.color=green, outsphere=glass, opacity=0.4
#Also, inner sphere: glass, color=gray, opacity=0.5, outsphere, glass, color=green, opacity=0.3
#Note: materials = {wood, rough, marble, plastic, earth, diffuse, emissive, unshaded, shiny, chrome, blazed, silver, BlueMarbe, bricks}
def node(name, pos, mass=default_mass, valence=base_color, lit=False, noosphere=default_mass/2, **kwargs):  #noosphere argument arbitrary
    """Draws a node on the screen.  Currently, a node is a sphere, plus an atmosphere."""
    label(pos=pos, text=name, box=False, opacity=0, color=color.gray(0.4), line=False, height=6)
    hsvcolor = vector(color.rgb_to_hsv(valence))
    if lit:  #primitve activity model:  make it a light source  #local_light(pos=pos, color=(1.0,0,0)) or at least maximize saturation #XXX is this working?
        local_light(pos=pos, color=color.white)
        hsvcolor[1] = 1 #maximize saturation at least.
    else:
        hsvcolor[2] *= 0.3 #reducing lightness
    valence = color.hsv_to_rgb(hsvcolor)
    sphere(pos=pos, color=valence, opacity=base_opacity, radius=mass, material=materials.emissive if lit else scene.material, **kwargs) #inner sphere  (Note: try material=chrome)
    sphere(pos=pos, color=atmos(valence), opacity=0.3*base_opacity, radius=mass+noosphere, material=materials.emissive, **kwargs) #outer sphere, color should be converted to hsv and value amplified assuming ambient color is shade of pure white

###################################################################

### Rotation should be tried...
##for i in arange(0,pi):
##    f.axis=(0,i,0)

##Experiment with crude fog (takes a few moments to load up a million points)
##l=[]
##for i in range(1000000):
##    l.append(rand3tuple())    
##points(pos=l, size=1, color=color.gray(scene.ambient), size_units="world")

## The actual drawing of spheres here
#local_light(pos=(0,0,0))
for i in range(num_nodes):
    light = (random() > 1 - p_nodes_lit)
    if light: print "lit"
    node(default_name+str(i), rand3tuple(), randint(1,default_mass), base_color, light, randint(default_mass/2, default_mass*2))

### Experiment in edge drawing
##nodes = scene.objects[:]
##for s in nodes:
##    tail=choice(nodes) #pick a random destination node
##    #cylinder(pos=s.pos, axis=tail.pos, radius=10, color=(0.2,0.2,0.1))
##    curve(pos=[s.pos, tail.pos], color=(0.1,0.1,0.1), radius=4, visible=False)

## Simple event handling, currently only can click nodes and affect radius
while True:
    rate(100)
    #f=scene.forward
    #print(scene.forward)
    if scene.mouse.events:
        mm=scene.mouse.getevent()
        if mm.pick==None: #create new sphere
            node("light", pos=mm.pos, lit=True)
        else:
            print mm.pick, mm.pick.radius
            if mm.shift:  #XXX this is crude need to send this to node object so it both spheres get adjusted
                mm.pick.radius-=1
            else:
                mm.pick.radius+=1
##    if scene.kb.keys:
##        key=scene.kb.getkey()
##        print key
##        #if key == "Left-Shift"

#cities={"Denver","Seattle","Portland","Boise","Fargo","LosAngeles"}
#g=Graph()
#print(g)
