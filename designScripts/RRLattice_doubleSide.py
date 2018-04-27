# ------------------------------------------------------------------ #
# RRLattice_doubleSide.py
# ------------------------------------------------------------------ #
#
# A series of Ring Resonator's for 3D printing testing purposes.
# Coupling is performed on both sides for higher density
#
# ------------------------------------------------------------------ #
# VERSION HISTORY
# 25 Apr 2018 - AMH - Initialization
# ------------------------------------------------------------------ #
#
# ------------------------------------------------------------------ #
#      To - DO
# ------------------------------------------------------------------ #
# Code cleanup
# Add bosch etch buffer off of floor plan
#
# ------------------------------------------------------------------ #
#      Import libraries
# ------------------------------------------------------------------ #

# Get project library path to import library files
import sys
import os
d = os.path.dirname(os.getcwd())
libPath = os.path.abspath(os.path.join(d, 'lib'))
sys.path.insert(0, libPath)

# Import all other libraries
import gdspy
import numpy as np
import objectLibrary as obLib

# ------------------------------------------------------------------ #
#      Initialize parent cell and set params
# ------------------------------------------------------------------ #

RRLatticeCell = gdspy.Cell('RRLattice')

# GDS Parameters
layerNumber = 1        # silicon layer number

# Chip parameters
chipDim = 8.78 * 1e3   # Width / height of our chip

# Waveguide parameters
waveguideWidth      = 0.5  # width of all our waveguides
waveguideBendRadius = 10   # bend radius for waveguides

# Coupler parameters
couplePitch         = 127     # separation distance between couplers
couplerBufferMiddle = 50      # distance from drop port to taper waveguide
couplerBufferBottom = 100     # distance from trhough port to taper waveguide
middleTapperHeightBuffer = 20 # distance from middle taper bus to bottom taper bus

# Ring parameters
ringRadius         = 0    # Starting ring radius
repeatRing         = 3     # Number of times to repeat ring radius
Rincrement         = 10    # Number of microns to increase next ring radius
ringGap            = 0.2   # Separation between ring and busses

# Taper Parameters
taperBufferWidth = 0.180;   # width of the buffer after taper
taperBufferLength = 5;      # length of the buffer after taper

# Text parameters
textBuffer = 20;      # distance from text to edge of chip and taper
textSize   = 15;      # base size of text

# Vernier parameters
vernierPadding = 0    # Pad the corner from the floor plan

# ------------------------------------------------------------------ #
#      Add a floor plan
# ------------------------------------------------------------------ #

# Add floor plan
RRLatticeCell.add(gdspy.Rectangle([0,0],[chipDim,-chipDim],layer=100))

# ------------------------------------------------------------------ #
#      Add Vernier Pattern
# ------------------------------------------------------------------ #

vernierCell = obLib.vernier(layerNumber)

# get dimensions of vernier pattern
vernierDims   = vernierCell.get_bounding_box()
vernierWidth  = abs(vernierDims[0,0] - vernierDims[1,0])
vernierHeight = abs(vernierDims[0,1] - vernierDims[1,1])

# Add vernier pattern
pos = (chipDim - (vernierPadding), -(vernierPadding))
RRLatticeCell.add(gdspy.CellReference(vernierCell,pos))

# ------------------------------------------------------------------ #
#      Create several rings along chip
# ------------------------------------------------------------------ #

# Number of RR given pitch
numRR = np.floor((chipDim-vernierHeight)/couplePitch)

# Vertical offset to begin couplers, due to Vernier pattern issues
couplerYOffset = vernierHeight

# Intialize coupling taper cell
couplingTaperCell = obLib.couplingTaper()

# Get dimensions of taper
taperDims   = couplingTaperCell.get_bounding_box()
taperWidth  = abs(taperDims[0,0] - taperDims[1,0])
taperHeight = abs(taperDims[0,1] - taperDims[1,1])

# Iterate through RR and draw system
incrementOffset = 0;      # used to determine when to repeat ring radius
for k in range(1,int(numRR)):

    # Iterate through all both couplers associated with one ring
    if k % 2 == 0:

        # Only draw up a new device if we are moving on to a new ring radius
        if incrementOffset % repeatRing == 0:
            ringRadius = ringRadius + Rincrement;
            ringCell   = gdspy.Cell("Ring_radius="+str(ringRadius));

            # Draw the ring
            ringCell.add(gdspy.Round(
                (0,0),inner_radius=ringRadius-waveguideWidth/2,
                radius=ringRadius+waveguideWidth/2,layer=layerNumber))

            # Draw the top bus
            ringCell.add(gdspy.Rectangle(
                (-1.5*ringRadius,ringRadius + waveguideWidth/2 + ringGap),
                (1.5*ringRadius,ringRadius + waveguideWidth/2 + ringGap + waveguideWidth),
                layer=layerNumber))

            # Draw the bottom bus
            ringCell.add(gdspy.Rectangle(
                (-1.5*ringRadius,-(ringRadius + waveguideWidth/2 + ringGap)),
                (1.5*ringRadius,-(ringRadius + waveguideWidth/2 + ringGap + waveguideWidth)),
                layer=layerNumber))

        # Initialize unit cell
        RingUnitCell = gdspy.Cell('RingUnit_'+str(k))

        # Get dimensions of the ring to align waveguides
        RingcellCDims   = ringCell.get_bounding_box()
        RingcellWidth   = abs(RingcellCDims[0,0] - RingcellCDims[1,0])
        RingcellHeight  = abs(RingcellCDims[0,1] - RingcellCDims[1,1])

        # add ring
        pos = (k*couplePitch,
               -k*couplePitch - RingcellHeight/2 + waveguideWidth/2 - couplerYOffset)
        RingUnitCell.add(gdspy.CellReference(ringCell,pos))

        # add termination taper to prevent reflections
        posTaper = (k*couplePitch + RingcellWidth/2 + taperWidth/2,
                    -k*couplePitch - RingcellHeight + waveguideWidth - couplerYOffset)
        RingUnitCell.add(gdspy.CellReference(couplingTaperCell,posTaper,rotation=180))

        # add left coupling taper
        posTaper = (taperWidth/2,-(k)*couplePitch - couplerYOffset)
        RingUnitCell.add(gdspy.CellReference(couplingTaperCell,posTaper))

        RingUnitCell.add(gdspy.Rectangle(
            [-taperBufferLength,-(k)*couplePitch+taperBufferWidth/2 - couplerYOffset],
            [0,-(k)*couplePitch-taperBufferWidth/2 - couplerYOffset],
            layer=layerNumber))

        # add right coupling tapers
        for ktaper in range(0,2):
            posTaper = (chipDim-taperWidth/2,-(k+ktaper)*couplePitch - couplerYOffset)
            RingUnitCell.add(gdspy.CellReference(couplingTaperCell,posTaper,rotation=180))

            RingUnitCell.add(gdspy.Rectangle(
                [chipDim+taperBufferLength,-(k+ktaper)*couplePitch+taperBufferWidth/2 - couplerYOffset],
                [chipDim,-(k+ktaper)*couplePitch-taperBufferWidth/2 - couplerYOffset],
                layer=layerNumber))

        # add text below coupling first taper on left
        text = gdspy.Text(str(int(ringRadius)), textSize,
                (textBuffer, -k*couplePitch - textBuffer - textSize/2 - couplerYOffset),
                layer=layerNumber)
        RingUnitCell.add(text)

        # add text below coupling first taper on right
        text = gdspy.Text(str(int(ringRadius)), textSize,
                (chipDim-taperWidth, -k*couplePitch - textBuffer - textSize/2 - couplerYOffset),
                layer=layerNumber)
        RingUnitCell.add(text)

        # connect top taper to coupler
        RingUnitCell.add(gdspy.Rectangle(
            [chipDim - taperWidth,-k*couplePitch + waveguideWidth/2 - couplerYOffset],
            [k*couplePitch + RingcellWidth/2, -k*couplePitch - waveguideWidth/2 - couplerYOffset],
            layer=layerNumber))

        # connect throughport to taper
        RingUnitCell.add(gdspy.Rectangle(
            [taperWidth,-k*couplePitch + waveguideWidth/2 - couplerYOffset],
            [k*couplePitch - RingcellWidth/2, -k*couplePitch - waveguideWidth/2 - couplerYOffset],
            layer=layerNumber
        ))

        # connect middle taper to coupler - Since we are worried about too small
        # of segments for our bend radius, we'll first route the waveguide
        # down towards the bottom waveguide, and then back up...just to be safe.
        stretch = chipDim - k*couplePitch + RingcellWidth/2
        sub1    = taperWidth
        travel  = couplePitch - middleTapperHeightBuffer
        sub2    = stretch - sub1
        length = [sub1,travel,sub2,
                  travel + couplePitch - RingcellHeight + waveguideWidth,
                  couplerBufferMiddle + 1]
        turn = [1,-1,-1,-1]
        l1path = gdspy.L1Path(initial_point=(chipDim-taperWidth, -(k+1)*couplePitch - couplerYOffset),
                              direction='-x', width=waveguideWidth, length=length,
                              turn=turn, layer=layerNumber)
        l1path.fillet(radius=waveguideBendRadius)
        RingUnitCell.add(l1path)

        # consolidate cells to master cell
        RRLatticeCell.add(gdspy.CellReference(RingUnitCell))

        incrementOffset = incrementOffset + 1

# ------------------------------------------------------------------ #
#      OUTPUT GDS FILE
# ------------------------------------------------------------------ #

# Output the layout to a GDSII file (default to all created cells).
# Set the units we used to micrometers and the precision to nanometers.

filename = 'RR_doubleSide.gds'
outPath = os.path.abspath(os.path.join(d, 'GDS/'+filename))
gdspy.write_gds(outPath, unit=1.0e-6, precision=1.0e-9)
