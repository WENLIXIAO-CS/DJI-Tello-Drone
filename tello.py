from threading import Thread
import numpy as np
import threading
import socket
import cv2
import re 

class Tello_basic :

    opt = {
        't' : b'takeoff' ,
        'y' : b'land' ,
        
        'a' : b'left 50' ,
        'd' : b'right 50' ,
        'w' : b'forward 50' ,
        's' : b'back 50' ,

        'i' : b'up 50' ,
        'k' : b'down 50' ,
        'j' : b'ccw 15' ,
        'l' : b'cw 15' , 

        'u' : b'flip l' ,
        'o' : b'flip r'
    }

    def __init__ (self) :
        self.send_addr = ( '192.168.10.1' , 8889 )
        self.host_port = ( '' , 9000 )

        self.sock = socket.socket ( socket.AF_INET , socket.SOCK_DGRAM )
        self.sock.bind ( self.host_port )

        self.thread_rev = threading.Thread ( target = self.tello_rev )
        self.thread_rev.start ()

        self.stack_opt = []
        self.flg_rev = 0
        self.rev_battery = None
        self.rev_speed = None

    
    def tello_rev ( self ) :
        while True :
            try :
                data , sever = self.sock.recvfrom ( 1024 )
                rev_info = data.decode ( encoding = 'UTF-8' )
                
                try :
                    f1 = re.findall ( '(\d+)' , str ( rev_info ) )
                    self.rev_battery = f1 [0]
                except :
                    print ( 'Tello feedback >' + rev_info )
                    pass
            except Exception :
                print ( 'Exit...' )
                break
    
    def stop_thread_rev ( self ) :
        self.sock.close ()

    def send_command ( self , str_command ) :
        try :
            self.stack_opt.append ( self.flg_rev ) 
            sent = self.sock.sendto ( str_command , self.send_addr )
            self.flg_rev = 0 
        except : 
            print ( 'error' )

    def access_SDK ( self ) :
        self.send_command ( b'command' ) 
    
    def stream_on ( self ) :
        self.send_command ( b'streamon' )

    def stream_off ( self ) :
        self.send_command ( b'streamoff' )
    
    def query_battery ( self ) :
        self.flg_rev = 1
        self.send_command ( b'battery?' )
    
    def query_speed ( self ) :
        self.flg_rev = 2
        self.send_command ( b'speed?' )

    def take_off ( self ) :
        self.send_command ( b'takeoff' )
    def land ( self ) :
        self.send_command ( b'land' )

class Tello_Video ( Tello_basic ) :
    def __init__ ( self ) :

        super ().__init__ ()

        self.video_IP = '0.0.0.0'
        self.video_PORT = 11111 
        self.video_addr = 'udp://@' + self.video_IP + ':' + str (self.video_PORT)

        self.grab , self.frame = ( None , None )
        self.stop_video = False
    
    def get_video_frame ( self ) :
        if self.frame is None :
            self.cap = cv2.VideoCapture ( self.video_addr )
            if self.cap.isOpened () is not True :
                self.cap.open ( self.video_addr )
            self.grab , self.frame = self.cap.read () 
            self.start_video_loop () 
        return self.frame 
    
    def start_video_loop ( self ) :
        thread_video = threading.Thread ( target = self.frame_update )
        thread_video.start ()

    def frame_update ( self ) :
        while self.stop_video != True :
            if not self.grab or not self.cap.isOpened () :
                self.stop_video = True
            else :
                self.grab , self.frame = self.cap.read () 

width =  600
height = 450

tello = Tello_Video () 

tello.access_SDK () 
tello.stream_off ()
tello.stream_on () 

while True :
    origin_frame = tello.get_video_frame ()
    origin_frame = cv2.resize( origin_frame, (width, height))
    tello.query_battery ()
    if tello.rev_battery is not None and tello.rev_battery.isdigit () :
        try :
            cv2.putText( origin_frame ,'battery:' + tello.rev_battery + '%',(50,50),cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,0) , 2)
        except :
            pass
    cv2.imshow ( 'origin' , origin_frame )
    num = cv2.waitKey (1)
    if num != -1 :
        if num == ord ( 'q' ) :
            cv2.destroyAllWindows ()
            tello.stop_thread_rev ()
            tello.stream_off ()
            break
        else :
            try :
                operation = chr ( num )
                str_command = tello.opt [ operation ]
                tello.send_command ( str_command )
            except :
                pass
