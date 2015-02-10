#
# Contouring routing based on the algorithm by Paul D. Bourke
# http://paulbourke.net/papers/conrec/
# and his Fortran 77 version http://paulbourke.net/papers/conrec/conrec_for.txt
#
# Modifications and additions by
# Fernando Cucchietti
# Scientific Visualization Group
# Barcelona Supercomputing Center
# 2015
#

usage = '''
Usage: \n
conrec(datamatrix, Xpositions, Ypositions, Levels) \n
Returns a list of lists, one collection of lists for each level in Levels: \n
[ [ [ [x1,y1],[x2,y2],... ], [ [x1,y1],[x2,y2],... ], ... ],  (list of curves for Levels[0] )
  [ [ [x1,y1],[x2,y2],... ], [ [x1,y1],[x2,y2],... ], ... ],  (list of curves for Levels[1] )
  ....
]
'''
print (usage)

import math
import json

def conrec(data,x,y,levels,format="PYTHON"):
    if (len(x) != len(data) or len(y) != len(data[0])):
        return None
    allpoints=[]
    im = [0,0,1,1,0]
    jm = [0,0,0,1,1]
    #    castab =[ [ [0,0,9], [0,1,5], [7,4,8] ],[ [0,3,6], [2,3,2], [6,3,0] ],[ [8,4,7], [5,1,0], [9,0,0] ] ] # Fortran Order
    castab = [ [0,0,8],[0,2,5],[7,6,9] ],[ [0,3,4],[1,3,1],[4,3,0] ],[ [9,6,7],[5,2,0],[8,0,0] ] # C ordering
    h  = [0.0,0.0,0.0,0.0,0.0]
    xh = [0.0,0.0,0.0,0.0,0.0]
    yh = [0.0,0.0,0.0,0.0,0.0]
    sh = [0,0,0,0,0]
    def xsect(p1,p2):
        return (1.0*h[p2]*xh[p1]-1.0*h[p1]*xh[p2])/(1.0*h[p2]-1.0*h[p1])
    def ysect(p1,p2):
        return (1.0*h[p2]*1.0*yh[p1]-1.0*h[p1]*1.0*yh[p2])/(1.0*h[p2]-1.0*h[p1])
    for j in range(len(data[0])-2,-1,-1):
        for i in range(len(x)-1):
            dmin =  min(min(min(data[i][j],data[i][j+1]),data[i+1][j]),data[i+1][j+1])
            dmax =  max(max(max(data[i][j],data[i][j+1]),data[i+1][j]),data[i+1][j+1])
            if (dmax >= levels[0] and dmin <= levels[-1] ):
                for level in levels:
                    if (level >= dmin and level <= dmax):
                        for m in range(4,-1,-1):
                            if (m > 0):
                                h[m]=data[i+im[m]][j+jm[m]]-level ##
                                xh[m]=x[i+im[m]] ##
                                yh[m]=y[j+jm[m]] ##
                            else:
                                h[0]=0.25*(h[1]+h[2]+h[3]+h[4])
                                xh[0]=0.5*(x[i]+x[i+1])
                                yh[0]=0.5*(y[j]+y[j+1])
                            if ( h[m] > 0.0):
                                sh[m]=1
                            elif( h[m] < 0.0):
                                sh[m]=-1
                            else:
                                sh[m]=0
                    #     Note: at this stage the relative heights of the corners and the
                    #c     centre are in the h array, and the corresponding coordinates are
                    #c     in the xh and yh arrays. The centre of the box is indexed by 0
                    #c     and the 4 corners by 1 to 4 as shown below.
                    #c     Each triangle is then indexed by the parameter m, and the 3
                    #c     vertices of each triangle are indexed by parameters m1,m2,and m3.
                    #c     It is assumed that the centre of the box is always vertex 2 though
                    #c     this isimportant only when all 3 vertices lie exactly on the same
                    #c     contour level, in which case only the side of the box is drawn.
                    #c
                    #c
                    #c           vertex 4 +-------------------+ vertex 3
                    #c                    | \               / |
                    #c                    |   \    m-3    /   |
                    #c                    |     \       /     |
                    #c                    |       \   /       |
                    #c                    |  m=2    X   m=2   |       the centre is vertex 0
                    #c                    |       /   \       |
                    #c                    |     /       \     |
                    #c                    |   /    m=1    \   |
                    #c                    | /               \ |
                    #c           vertex 1 +-------------------+ vertex 2
                    #c
                    #c
                    #c
                    #c                    Scan each triangle in the box
                    for m in range(1,5):
                        m1=m
                        m2=0
                        if(m != 4):
                            m3=m+1
                        else:
                            m3=1
                        case = castab[ sh[m1]+1][ sh[m2]+1 ][ sh[m3]+1 ]
                        if (case==1):
                            x1 = xh[m1];
                            y1 = yh[m1];
                            x2 = xh[m2];
                            y2 = yh[m2];
                        elif (case==2):
                            #case 2: /* Line between vertices 2 and 3 */
                            x1 = xh[m2];
                            y1 = yh[m2];
                            x2 = xh[m3];
                            y2 = yh[m3];
                        elif (case==3):
                            # case 3: /* Line between vertices 3 and 1 */
                            x1 = xh[m3];
                            y1 = yh[m3];
                            x2 = xh[m1];
                            y2 = yh[m1];
                        elif (case==4):
                            #case 4: /* Line between vertex 1 and side 2-3 */
                            x1 = xh[m1];
                            y1 = yh[m1];
                            x2 = xsect(m2,m3);
                            y2 = ysect(m2,m3);
                        elif (case==5):
                            #case 5: /* Line between vertex 2 and side 3-1 */
                            x1 = xh[m2];
                            y1 = yh[m2];
                            x2 = xsect(m3,m1);
                            y2 = ysect(m3,m1);
                        elif (case==6):
                            # case 6: /* Line between vertex 3 and side 1-2 */
                            x1 = xh[m3];
                            y1 = yh[m3];
                            x2 = xsect(m1,m2);
                            y2 = ysect(m1,m2);
                        elif (case==7):
                            # case 7: /* Line between sides 1-2 and 2-3 */
                            x1 = xsect(m1,m2);
                            y1 = ysect(m1,m2);
                            x2 = xsect(m2,m3);
                            y2 = ysect(m2,m3);
                        elif (case==8):
                            # case 8: /* Line between sides 2-3 and 3-1 */
                            x1 = xsect(m2,m3);
                            y1 = ysect(m2,m3);
                            x2 = xsect(m3,m1);
                            y2 = ysect(m3,m1);
                        elif (case==9):
                            #case 9: /* Line between sides 3-1 and 1-2 */
                            x1 = xsect(m3,m1);
                            y1 = ysect(m3,m1);
                            x2 = xsect(m1,m2);
                            y2 = ysect(m1,m2);
                        if (case !=0 ):
                            allpoints.append([[x1,y1],[x2,y2],level])
    EPSILON = 1.0e-15 ## Zero distance between points = below numerical error
    def dist(p1,p2):
        return math.sqrt( (p1[0]-p2[0])**2 + (p1[1]-p2[1])**2 )
    fullout = []    # We will reformat the output from the classical routine
    for level in levels:
        levelsegments = [] #collect all segments in a given level
        for point in allpoints:
            if (point[2]==level):
                levelsegments.append([point[0],point[1]])
        cleanlist=[]
        while (len(levelsegments)>0): # this should iterate through all separate paths
            apath=levelsegments.pop() #remove the last one and start looking for connections
            print (apath)
            idx=0
            while (idx<len(levelsegments)):
                segment = levelsegments[idx]
                if (dist(apath[0], segment[1])<EPSILON): #segment points to our path
                    segment = levelsegments.pop(idx) #remove from the searchable list
                    apath.insert(0,segment[0])
                elif(dist(apath[-1],segment[0])): #our path continues on segment
                    segment = levelsegments.pop(idx) #remove from the searchable list
                    apath.append(segment[1])
                else:
                    idx=idx+1
            cleanlist.append(apath)
        fullout.append([level,cleanlist])
    if (format=="JSON"):
        jsonout = []
        for output in fullout:
            paths=[]
            for path in output[1]:
                jsonpath = []
                for point in path:
                    jsonpath.append({'x': point[0], 'y': point[1]})
                paths.append(jsonpath)
            jsonout.append( { 'level': output[0], 'paths': paths } )
        return json.dumps(jsonout)
    else:
        return fullout
                    
# Example for testing
# data = [[0.0, 1.0, 0.0], [1.0, 2.0, 1.0], [0.0, 1.0, 0.0]]
# a=conrec(data, [1.0, 2.0, 3.0], [1.0, 2.0, 3.0], [0.5, 1.0, 2.5],"JSON")
# print (a)
