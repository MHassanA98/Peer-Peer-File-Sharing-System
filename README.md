# Peer-Peer-File-Sharing-System

## Introduction
In this assignment, you will build a peer-peer file sharing system. Your system will be a Distributed
Hash Table (DHT) based key-value storage system that has only two basic operations; **put()** and
**get()**. put() operation takes as input a filename, evaluates its key using some hash function, and
places the file on one of the nodes in the distributed system. Whereas, get() function takes as input a
filename, finds the appropriate node that can potentially have that file and returns the file if it exists
on that node. We will make this system failure tolerant i.e. it should not lose any data in case of
failure of a node.

You will be building the DHT using consistent hashing. Consistent hashing is a scheme for
distributing key-value pairs, such that distribution does not depend upon number of nodes in the
DHT. This allows to scale the size of DHT easily i.e. addition or removal of new nodes in the system
is not a costly operation.

## Background
For extra resources, you are welcome to look at the following articles:

• Consistent Hashing - System Design Blog

https://medium.com/system-design-blog/consistent-hashing-b9134c8a9062

• A Guide to Consistent Hashing

https://www.toptal.com/big-data/consistent-hashing

These articles go in a little extra detail of having virtual nodes for better load balancing. Since, you
would not be implementing that in this assignment, you can ignore it.

## Provided code

### DHT.py Explanation:

1. Node() : Initialization of Node, you may maintain any state you need here. Following
variables which are already declared should not be renamed and should be set appropriately
since testing will take place through them. Some of them have already been set to
appropriate values.

    a. **host**: Save hostname of Node e.g. localhost

    b. **port**: Save port of Node e.g. 8000

    c. **M**: hash value’s number of bits
    
    d. **N**: Size of the ring
    
    e. **key**: it is the hashed value of Node
    
    f. **successor**: Next node’s address (host, port)
    
    g. **predecessor**: Previous node’s address (host, port)
    
    h. **files**: Files mapped to this node
    
    i. **backUpFiles**: Files saved as back up on this node

2. **join()** :

This function handles the logic for a new node joining the DHT: this function should update
node’s successor and predecessor. It should also trigger the update of affected nodes’ (i.e.
successor node and predecessor node) successor and predecessor too. Finally, the node
should also get its share of files.

3. **leave()** :

Calling leave should have the following effects: removal of node from the ring and transfer
of files to the appropriate node.

4. **put()** :

This function should handle placement of file on appropriate node; save the files in the
directory for the node.

5. **get()** :

This function is responsible for looking up and getting a file from the network.

Some functions have already been provided to you as utility functions. You can also create more
helper functions.

1. **hasher()** :
Hashes a string to an M bits long number. You should use it as follows:

    i. For a node: hasher(node.host+str(node.port))

    ii. For a file: hasher(filename)

2. **listener()** :

This function listens for new incoming connections. For every new connection, it spins a new
thread handleConnection to handle that connection. You may write any necessary logic for
any connection there.

3. **sendFile()** :

You can use this function to send a file over the socket to another node.

4. **receiveFile()** :

This function can be used to receive files over the socket from other nodes. Both these
functions have the following arguments:

    a. soc: A TCP socket object.
    b. fileName: File’s name along with complete path e.g. “CS382/PA3/file.py

## Implementation instructions

Note: You are required to use sockets for any communication between the nodes i.e. you should not
access another node’s variables or functions directly.

### 1- Initialization:

When a new node is created, its successor and predecessor do not point to any other node as it does
not know any other node yet. In this case both these pointers should point to the node itself.
successor and predecessor both store a tuple of host and port e.g. (“localhost”, 20007).

### 2 -Join:

Before you implement join, put or get; it is a good idea to implement a look-up function. This lookup function should be able to find the node responsible for a given key. Benefit of doing this is that you can reuse this function in join, put and get.

Let’s come to join now. Join function takes as input the address (host, port) of a node (joiningAddr)
already present in the DHT. You will connect with this node and ask it to do a lookup for the new 
node’s successor and update the new node’s successor based on the response. You should also write
the logic of updating the predecessor. This usually happens through pinging; a node keeps pinging
(after around 0.5 second) its successor to know whether it is still its successor’s predecessor. If the
successor node has updated its predecessor, this node should update its successor to the current
successor’s predecessor. The joining process is explained through the figures below.

<div align="center" >
    <img src="/image/DHT_Join.png" width="700px"</img> 
</div>

You should pay special attention to corner cases such as when there is only one node in the system;
in this case, instead of the joining address, an empty string will be passed. Similarly, when there are
only two nodes, they will be each other’s successor and predecessor.

### 3 - Put and Get:

When put is called on a node with a file, it finds the node responsible for that file and sends the file
to that node. You can use sendFile and receiveFile functions here. You should store the file in the
directory assigned to that node given by node’s host and port as host_port e.g. localhost_20007. This
directly is already made in the provided starter code.

Similarly, the get method should again first find the node responsible for the file and then retrieve
the file from that node. Again, you can use sendFile and receiveFile functions. This time you should 
get the file from the node and save it in the current directory. If the file exists you should return the
filename, if it does not you should return None.

Every node is responsible for the space between itself and its predecessor, See the following figure
for a better understanding.

<div align="center" >
    <img src="/image/DHT_PutGet.png" width="700px"</img> 
</div>

### 4 - File Transfer on Join:

When a new node joins the network, it should get its share of files i.e. the files that hash to its space.
Think about what file will come in share of a new node. After transferring the file, the new node will
be responsible for all these files and the previous responsible node should delete these files from its
list.

### 5 - Leave:

When a node leaves the DHT, it should do so gracefully. This means it should tell its predecessor
that it is leaving, communicate with the predecessor, the address of its successor node so the
predecessor can update its successor. Moreover, leaving node should also send all its files to the new
responsible node. Think about which node will be responsible for these files now.

### 6 - Failure Tolerance:

As we talked earlier, we need to make our system tolerant to node failures. Failures are
commonplace in real life systems, in fact, most designs are made keeping failures in mind as a
requirement. We also want our DHT to be resilient to failures. Firstly, you should be able to detect
that a node is down, typically this is done by pinging a node. Since we are already pinging the
successor, we can check if the successor does not respond for 3 consecutive pings, this means the
successor node is down. You will need to keep some state in advance to account for failure. For
example, to maintain the ring structure of DHT, every node should keep a list of successors instead
of immediate successor. In case the immediate successor is detected to have failed, we can update
our immediate successor to the next successor in our list. You may just keep the state of the second
successor instead of keeping a list of successors for this assignment. Next you want to replicate all
the files so that even if a node fails, no data is lost. Think about where you should replicate files? At
the predecessor of the node? At the successor? At the start of the DHT.py file mention where you
replicated files and argue why.

## Running and Testing
Test cases are run in the order described here. You may not be able to test one part before
completing its previous parts as most of the parts have previous parts as their pre-requisite. You will
need Python3 to run this file, you can run the tests on any OS but Linux preferable. Use the
following command to run the tests:

**python3 check.py <port>**

You should pass a port between 1000 and 65500. If you start getting an error like:

**error: [Errno 48] Address already in use**

Just choose a different port number with a significant gap. Or alternatively, restart the terminal.


***If you believe something needs to be changed in my code, you may create a pull request. I'd be glad to review your suggested change*** 😄
