#!/usr/bin/env python 
"""
layer2png.py

Copyright (C) 2007-2009 Matt Harrison, matthewharrison [at] gmail.com

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA



A script that slices images.  It might be useful for web design.

You pass it the name of a layer containing rectangles that cover
the areas that you want exported (the default name for this layer
is "slices").  It then sets the opacity to 0 for all the rectangles
defined in that layer and exports as png whatever they covered.
The output filenames are based on the "Id" field of "Object Properties"
right click contextual menu of the rectangles.

One side effect is that after exporting, it sets the slice rectangles
to red with a 25% opacity.  (If you want to hide them, just click on the
eye next to the layer).

For good pixel exports set the Document Properties, default units to "px"
and the width/height to the real size. (I use 1024x768)

"""
import os
import sys
import logging
import tempfile

try:
    from subprocess import Popen, PIPE
    bsubprocess = True
except:
    bsubprocess = False
    
try:
    import xml.etree.ElementTree as et
except ImportError, e:
    try:
        from lxml import etree as et
    except:
        sys.exit(_('The fantastic lxml wrapper for libxml2 is required by inkex.py and therefore this extension. Please download and install the latest version from http://cheeseshop.python.org/pypi/lxml/, or install it through your package manager by a command like: sudo apt-get install python-lxml'))

sys.path.append('/usr/share/inkscape/extensions')

import inkex
import simplestyle

logging.basicConfig(filename=os.path.join(tempfile.gettempdir(), 'inklog.log'), level=logging.DEBUG)

class ExportSlices(inkex.Effect):
    """Exports all rectangles in the current layer"""
    def __init__(self):
        inkex.Effect.__init__(self)
        self.OptionParser.add_option("--tab",
                                     action="store", type="string", 
                                     dest="tab", default="sampling",
                                     help="The selected UI-tab when OK was pressed")
        self.OptionParser.add_option("-d", "--directory",
                                     action="store", type="string", 
                                     dest="directory", default=os.path.expanduser("~"),
                                     help="Existing destination directory")
        self.OptionParser.add_option("-l", "--layer",
                                     action="store", type="string",
                                     dest="layer_name", default="slices",
                                     help="Layer with slices (rects) in it")
        self.OptionParser.add_option("-o", "--overwrite",
                                     action="store", type="inkbool", default=False,
                                     help="Overwrite existing exports?")
        
    def effect(self):
        logging.log(logging.DEBUG, "COMMAND LINE %s" % sys.argv)
        # set opacity to zero in slices
        for node in self.get_layer_nodes(self.document, self.options.layer_name):
            self.clear_color(node)

        # save new xml
        fout = open(self.args[-1], 'w')
        self.document.write(fout)
        fout.close()

        # in case there are overlapping rects, clear them all out before
        # saving any
        for node in self.get_layer_nodes(self.document, self.options.layer_name):
            self.export_node(node)

        #change slice colors to pink and set opacity to 25% in real document
        for node in self.get_layer_nodes(self.document, self.options.layer_name):
            self.pink_color(node)

    def get_layer_nodes(self, document, layer_name):
        """
        given an xml document (etree), and the name of a layer one
        that contains the rectangles defining slices, return the nodes
        of the rectangles.
        """
        #get layer we intend to slice
        slice_node = None
        slice_layer = document.findall('{http://www.w3.org/2000/svg}g')
        for node in slice_layer:
            label_value = node.attrib.get('{http://www.inkscape.org/namespaces/inkscape}label', None)
            if label_value == layer_name:
                slice_node = node

        if slice_node is not None:     
            return slice_node.findall('{http://www.w3.org/2000/svg}rect')
        return []

    def clear_color(self, node):
        '''
        set opacity to zero, and stroke to none

        Node looks like this:
        <rect
        style="opacity:0;fill:#eeeeec;fill-opacity:1;stroke:none;stroke-width:4.00099993;stroke-linecap:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1;display:inline"
        '''
        self.update_node_attrib(node, 'style', {'stroke':'none', 'opacity':'0'})

    def pink_color(self, node):
        """
        set color to red and opacity to 25%
        
        """
        self.update_node_attrib(node, 'style', {'fill':'#ff0000', 'opacity':'.25'})

    def update_node_attrib(self, node, attrib_name, attribs_to_overwrite):
        """
        svg style is overloaded with a dictlike value:
        <rect
       style="opacity:0;fill:#eeeeec;fill-opacity:1;stroke:none;stroke-width:4.00099993;stroke-linecap:round;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1;display:inline"
        """
        style = node.attrib[attrib_name]
        value_dict = simplestyle.parseStyle(style)
        for key, value in attribs_to_overwrite.items():
            value_dict[key] = value
        new_value = simplestyle.formatStyle(value_dict)
        node.attrib[attrib_name] = new_value
  
        
    def export_node(self, node):
        """
        Get the id attribute from the node and export it using the id as a name
        """
        svg_file = self.args[-1]
        node_id = node.attrib['id']
        name = "%s.png" % node_id
        directory = self.options.directory
        filename = os.path.join(directory, name)
        if self.options.overwrite or not os.path.exists(filename):
            command = "inkscape -i %s -e %s %s " % (node_id, filename, svg_file)
            if bsubprocess:
                p = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
                return_code = p.wait()
                f = p.stdout
                err = p.stderr
            else:
                _, f, err = os.open3(command)
            logging.log(logging.DEBUG, "COMMAND %s" % command)
            f.close()
        else:
            logging.log(logging.DEBUG, "Export exists (%s) not overwriting" % filename)

def _main():

    e = ExportSlices()
    e.affect()
    
if __name__ == "__main__":
    _main()
