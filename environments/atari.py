import copy
import datetime
import os

import cv2
import dqn.interfaces
import numpy as np
import pygame
from ale_python_interface import ALEInterface

class AtariEnvironment(dqn.interfaces.Environment):

    def __init__(self, atari_rom, frame_skip=4, noop_max=30, terminate_on_end_life=False, random_seed=123,
                 frame_history_length=4, use_gui=False, max_num_frames=500000, repeat_action_probability=0.0):
        self.ale = ALEInterface()
        self.ale.setInt('random_seed', random_seed)
        self.ale.setInt('frame_skip', 1)
        self.ale.setFloat('repeat_action_probability', 0.0)
        self.ale.setInt('max_num_frames_per_episode', max_num_frames)
        self.ale.loadROM(atari_rom)
        self.frame_skip = frame_skip
        self.repeat_action_probability = repeat_action_probability
        self.noop_max = noop_max
        self.terminate_on_end_life = terminate_on_end_life
        self.current_lives = self.ale.lives()
        self.is_terminal = False
        self.previous_action = 0
        self.num_actions = len(self.ale.getMinimalActionSet())

        w, h = self.ale.getScreenDims()
        self.screen_width = w
        self.screen_height = h
        self.zero_last_frames = [np.zeros((84, 84), dtype=np.uint8), np.zeros((84, 84), dtype=np.uint8)]
        self.last_two_frames = copy.copy(self.zero_last_frames)
        self.zero_history_frames = [np.zeros((84, 84), dtype=np.uint8) for i in range(0, frame_history_length)]
        self.frame_history = copy.copy(self.zero_history_frames)
        atari_actions = self.ale.getMinimalActionSet()
        self.atari_to_onehot = dict(zip(atari_actions, range(len(atari_actions))))
        self.onehot_to_atari = dict(zip(range(len(atari_actions)), atari_actions))
        self.screen_image = np.zeros(self.screen_height * self.screen_width, dtype=np.uint8)

        self.use_gui = use_gui
        self.original_frame = np.zeros((h, w), dtype=np.uint8)
        self.refresh_time = datetime.timedelta(milliseconds=1000 / 60)
        self.last_refresh = datetime.datetime.now()
        if (self.use_gui):
            self.gui_screen = pygame.display.set_mode((w, h))

    def getRAM(self, ram=None):
        return self.ale.getRAM(ram)

    def _get_frame(self):
        self.ale.getScreenGrayscale(self.screen_image)
        image = self.screen_image.reshape([self.screen_height, self.screen_width, 1])
        self.original_frame = image
        image = cv2.resize(image, (84, 84))
        return image

    def perform_action(self, onehot_index_action):
        if self.repeat_action_probability > 0:
            if np.random.uniform() < self.repeat_action_probability:
                onehot_index_action = self.previous_action
            self.previous_action = onehot_index_action
        action = self.onehot_to_atari[onehot_index_action]
        state, action, reward, next_state, self.is_terminal = self.perform_atari_action(action)
        return state, onehot_index_action, reward, next_state, self.is_terminal

    def perform_atari_action(self, atari_action):
        state = self.get_current_state()
        reward = self._act(atari_action, self.frame_skip)

        if self.use_gui:
            self.refresh_gui()

        self.frame_history[:-1] = self.frame_history[1:]
        self.frame_history[-1] = np.max(self.last_two_frames, axis=0)
        next_state = self.get_current_state()

        return state, atari_action, reward, next_state, self.is_terminal

    def _act(self, ale_action, repeat):
        reward = 0
        for i in range(repeat):
            reward += self.ale.act(ale_action)
            if i >= repeat - 2:
                self.last_two_frames = [self.last_two_frames[1], self._get_frame()]

        self.is_terminal = self.ale.game_over()

        # terminate the episode if current_lives has decreased
        lives = self.ale.lives()
        if self.current_lives != lives:
            if self.current_lives > lives and self.terminate_on_end_life:
                self.is_terminal = True
            self.current_lives = lives

        return reward

    def get_current_state(self):
        #return copy.copy(self.frame_history)
        return [x.copy() for x in self.frame_history]

    def get_actions_for_state(self, state):
        return [self.atari_to_onehot[a] for a in self.ale.getMinimalActionSet()]

    def reset_environment(self):
        self.last_two_frames = [self.zero_history_frames[0], self._get_frame()]

        if self.terminate_on_end_life:
            if self.ale.game_over():
                self.ale.reset_game()
        else:
            self.ale.reset_game()

        self.current_lives = self.ale.lives()

        if self.noop_max > 0:
            num_noops = np.random.randint(self.noop_max + 1)
            self._act(0, num_noops)

        self.previous_action = 0
        self.frame_history = copy.copy(self.zero_history_frames)
        self.frame_history[-1] = np.max(self.last_two_frames, axis=0)

        if self.use_gui:
            self.refresh_gui()

    def is_current_state_terminal(self):
        return self.is_terminal

    def refresh_gui(self):
        current_time = datetime.datetime.now()
        if (current_time - self.last_refresh) > self.refresh_time:
            self.last_refresh = current_time

            gui_image = np.tile(np.transpose(self.original_frame, axes=(1, 0, 2)), [1, 1, 3])
            # gui_image = np.zeros((self.screen_width, self.screen_height, 3), dtype=np.uint8)
            # channel = np.random.randint(3)
            # gui_image[:,:,channel] = np.transpose(self.original_frame, axes=(1, 0, 2))[:,:,0]

            pygame.surfarray.blit_array(self.gui_screen, gui_image)
            pygame.display.update()
