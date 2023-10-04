import os
import filecmp
import shutil
from stat import *
import time
import sys

class Sync:

    def __init__(self,logfile):
        self.node_list = []
        self.log_file=logfile

    def _log(self,txt):
        f=open(self.log_file,"a")
        f.write(txt + '\n')
        f.close()

    def add_node(self, node):
        self.node_list.append(node)

    def compare_nodes(self):
        ''' This method takes the nodes in the node_list and compares them '''
        # For each node in the list
        for node in self.node_list:
            # If the list has another item after it, compare them
            if self.node_list.index(node) < len(self.node_list) - 1: 
                node2 = self.node_list[self.node_list.index(node) + 1]
                # Passes the two root directories of the nodes to the recursive _compare_directories.
                self._compare_directories(node.root_path, node2.root_path)
    
    def _compare_directories(self, left, right):
        ''' This method compares directories. If there is a common directory, the
            algorithm must compare what is inside of the directory by calling this
            recursively.
        '''
        comparison = filecmp.dircmp(left, right)
        if comparison.common_dirs:
            for dir in comparison.common_dirs:
                self._compare_directories(os.path.join(left, dir), os.path.join(right, dir))
        if comparison.left_only:
            self._copy(comparison.left_only, left, right)
        if comparison.right_only:
            self._delete(comparison.right_only, right)
        left_newer = []
        right_newer = []
        if comparison.diff_files:
            for dir in comparison.diff_files:
                l_modified = os.stat(os.path.join(left, dir)).st_mtime
                r_modified = os.stat(os.path.join(right, dir)).st_mtime
                if l_modified > r_modified:
                    left_newer.append(dir)
                else:
                    right_newer.append(dir)
        self._copy(left_newer, left, right)
        self._delete(right_newer, right)

    def _copy(self, file_list, source, replica):
        ''' This method copies a list of files/directories from a source node to a destination node '''
        for f in file_list:
            srcpath = os.path.join(source, os.path.basename(f))
            if os.path.isdir(srcpath):
                shutil.copytree(srcpath, os.path.join(replica, os.path.basename(f)))
                self._log ('Copied directory \"' + os.path.basename(srcpath) + '\" from \"' + os.path.dirname(srcpath) + '\" to \"' + replica + '\"')
            else:
                shutil.copy2(srcpath, replica)
                self._log ('Copied \"' + os.path.basename(srcpath) + '\" from \"' + os.path.dirname(srcpath) + '\" to \"' + replica + '\"')
    
    def _delete(self, file_list, source):
        ''' This method deletes a files/directories  from a source node'''
        for f in file_list:
            srcpath = os.path.join(source, os.path.basename(f))
            if os.path.isdir(srcpath):
                shutil.rmtree(srcpath)
                self._log ('Deleted directory \"' + os.path.basename(srcpath) + '\" from \"' + os.path.dirname(srcpath) + '\" to \"' + source + '\"')
            else: 
                os.remove(srcpath)
                self._log ('Deleted file \"' + os.path.basename(srcpath) + '\" from \"' + os.path.dirname(srcpath) + '\" to \"' + source + '\"')

class Node:
    ''' This class represents a node in a synchronization '''  
    def __init__(self, path):
        self.root_path = os.path.abspath(path)
        self.file_list = os.listdir(self.root_path)

if __name__ == "__main__":
    source= sys.argv[1]
    replica= sys.argv[2]
    period= int(sys.argv[3])
    logfile= sys.argv[4]
    while True:
        sync = Sync(logfile)
        node1 = Node(source)
        node2 = Node(replica)
        sync.add_node(node1)
        sync.add_node(node2)
        print('Running sync')
        sync.compare_nodes()
        time.sleep(period)
        print('Sync done')

