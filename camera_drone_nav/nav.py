import rclpy
from rclpy.node import Node
from tf2_msgs.msg import TFMessage
from enum import Enum, auto
import pygame
from typing import Tuple
from pathlib import Path
from time import sleep
from geometry_msgs.msg import TransformStamped

class NavigationState(Enum):
    START = auto()
    SET_TARGET = auto()
    MOVE_UP = auto()
    MOVE_X = auto()
    MOVE_Y = auto()
    MOVE_Z = auto()
    MOVEMENT_DONE = auto()

class CameraDroneNavigationNode(Node):
    # Origin defined as the center of ID4
    tag_by_pos = {
        "ID0": (-2.2*.0254, 2.1*.0254),
        "ID1": (-2.2*.0254, -2.1*.0254),
        "ID2": (2.2*.0254, -2.1*.0254),
        "ID3": (2.2*.0254, 2.1*.0254),
        "ID4": (0, 0),
    }
    letter_by_pos = {
        "A": (-2.2*.0254, 0),
        "B": (0, 2.1*.0254),
        "C": (2.2*.0254, 0),
        "D": (0, -2.1*.0254),
    }
    
    # Letters to be navigated to
    destinations = ["A", "B"]
    
    def __init__(self):
        super().__init__("camera_drone_navigation_node")
        self.create_subscription(TFMessage, "tf", self.process_tf, 10)
        self.timer = self.create_timer(2, self.run_loop)
        
        self.state = NavigationState.START
        self.assets_dir = str(Path(__file__).parent / "audio_assets")

        self.current_tf: TransformStamped = None
        self.current_pose: Tuple[float, float] = None
        self.target_pose: Tuple[float, float] = None
        self.target_letter: str = None
        
        
        # Number of letters already completed
        self.destination_counter = 0
        
        pygame.init()
        pygame.mixer.init()
        
        
    def process_tf(self, msg: TFMessage):
        # Only use data from the first tag
        if msg.transforms:
            self.current_tf = msg.transforms[0]
        else:
            self.current_tf = None
    
    def update_pose_with_tf(self):
        tag_x = self.current_tf.transform.translation.x
        tag_y = self.current_tf.transform.translation.y
        tag_offset_x, tag_offset_y = self.tag_by_pos[self.current_tf.child_frame_id]
    
        self.current_pose = [-tag_x + tag_offset_x, tag_y + tag_offset_y]
    
    def play_audio(self, filename):
        pygame.mixer.music.load(f"{self.assets_dir}/{filename}.mp3")
        pygame.mixer.music.play()
    
    def run_loop(self):
        if self.state == NavigationState.START:
            if self.current_tf:
                self.update_pose_with_tf()
                self.state = NavigationState.SET_TARGET
            else:
                self.play_audio("none")
        elif self.state == NavigationState.SET_TARGET:
            if self.destination_counter < len(self.destinations):
                self.target_letter = self.destinations[self.destination_counter]
                self.target_pose = self.letter_by_pos[self.target_letter]
                self.state = NavigationState.MOVE_UP
            else:
                self.state = NavigationState.MOVEMENT_DONE
        elif self.state == NavigationState.MOVE_UP:
            if self.current_tf and self.current_tf.transform.translation.z > 0.1:
                self.state = NavigationState.MOVE_X
            else:
                self.play_audio("up")
        elif self.state in [NavigationState.MOVE_X, NavigationState.MOVE_Y]:
            if self.current_tf:
                self.update_pose_with_tf()
            if self.state == NavigationState.MOVE_X:
                if self.current_pose[0] < self.target_pose[0]:
                    self.play_audio("right")
                else:
                    self.play_audio("left")
                if abs(self.current_pose[0] - self.target_pose[0]) < 0.025:
                    self.state = NavigationState.MOVE_Y
            elif self.state == NavigationState.MOVE_Y:
                if self.current_pose[1] < self.target_pose[1]:
                    self.play_audio("forward")
                else:
                    self.play_audio("backward")
                if abs(self.current_pose[1] - self.target_pose[1]) < 0.025:
                    self.state = NavigationState.MOVE_Z
        elif self.state == NavigationState.MOVE_Z:
            self.play_audio("down")
            # Using sleeps since the april tag goes out of frame as the
            # drone is lowered
            sleep(4)            
            self.play_audio("reached")

            self.destination_counter += 1
            self.state = NavigationState.SET_TARGET
        elif self.state == NavigationState.MOVEMENT_DONE:
            self.play_audio("success")
            rclpy.shutdown()
        else:
            raise ValueError(f"Uknown State: {self.state.name}")
    
def main(args=None):
    rclpy.init(args=args)
    node = CameraDroneNavigationNode()
    rclpy.spin(node)
    rclpy.shutdown()