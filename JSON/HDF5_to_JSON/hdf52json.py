import json
import h5py

print ("Usage:   hdf5tojson(HDF5_filename [,True for verbosity]). Returns a JSON dump")

Verbose = False

def traverse_node(node):
    mydict = {}

    attrDict = {}
    for attr in node.attrs.keys():
        if Verbose: print "Reading attribute "+attr
        attrDict[ attr ] = node.attrs[attr].tolist()        
    mydict [ "attrs" ] = attrDict

    groupsDict = {}
    setsDict = {}
    numSets = 0
    for key in node.keys():
        if (type(node[key]) is h5py._hl.dataset.Dataset):
            if Verbose: print "Reading key "+key
            numSets=numSets+1
            if numSets > 20:
                break
            setattrs = {}
            for attr in node[key].attrs.keys():
                setattrs[ attr ] = node[key].attrs[attr].tolist()
                if Verbose: print ("Read set: "+str(numSets))
            setsDict[ node[key].name ] = {"attrs" : setattrs, "values" : node[key][()].tolist() }
        elif (type(node[key]) is h5py._hl.group.Group):
            if Verbose: print "Entering key "+key
            groupsDict[ node[key].name ] = traverse_node(node[key])
    mydict[ "datasets" ] = setsDict
    mydict[ "subgroups" ]  = groupsDict

    return mydict

def hdf5tojson(filename, verbose=False):
    with h5py.File(filename,'r') as general:
        Verbose=verbose
        return json.dumps (traverse_node(general) , sort_keys=True)

