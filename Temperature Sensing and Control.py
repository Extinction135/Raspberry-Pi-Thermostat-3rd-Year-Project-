import RPi.GPIO as GPIO
import matplotlib.pyplot as plt
import glob
import csv
import time
import os

# Load required drivers
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

# Define sensor's output file
temp_file = "sys/bus/w1/devices/28-000005e2fdc3/w1_slave" # Use own serial code

# Define sensor's output file
base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
temp_file = device_folder + '/w1_slave'

class HotPi:

    # Initialisation function
    def __init__(self):

        self.I = 0 # Initialise integrator
        self.prev_error = 0 # Previous error
        print "Please choose the desired temperature in celcius..."
        self.temp = []
        self.fw = csv.writer(open("temp_data.csv", 'a')) # Open CSV file
        self.PWM() # Start Pulse Width Modulation

    # Creating a function for Pulse Width Modulation
    def PWM(self):

        self.chan = 35 # Setting GPIO channel
        self.freq = 0.1 # Setting frequency
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.chan, GPIO.OUT) # Setting up a channel to be utilised
        self.p = GPIO.PWM(self.chan, self.freq) # Creating instance with specified frequency
        self.p.start(0) # Start PWM with zero duty cycle (no power)
        self.T = float(raw_input())

        while True:
            try:
                self.temp_raw()
                self.read_temp()
                self.PID()
                self.p.ChangeDutyCycle(self.dc) # To control the amount of power
                self.Data() # Store data
                print self.temp_c, self.U, self.dc, self.P, self.I, self.D
                time.sleep(5)

            except KeyboardInterrupt:
                self.p.stop() # Stop PWM
                GPIO.cleanup() #Reset GPIO
                self.fw.close()
                self.Plot()

    # Creating a function to read the sensor file
    def temp_raw(self):

        self.fr = open(temp_file, 'r') # Creating file handle
        self.lines = self.fr.readlines()  # Read the file and split by lines
        self.fr.close() # Close the file
        return self.lines

    # Creating a function to check temperature has been received and perform calculations
    def read_temp(self):

        self.signal = self.lines[0].strip()[-3:] # Get the last three characters
        while self.signal != 'YES': # Check for 'YES' signal
            time.sleep(1) # Sleep if not received
            self.signal = self.lines[0].strip()[-3:]

        self.temp_output = self.lines[1].find('t=') # Find temperature output
        if self.temp_output != -1: # Check for error
            self.temp_string = self.lines[1].strip()[self.temp_output+2:] # Get data only
            self.temp_c = float(self.temp_string) / 1000 # Convert to celsius
            return self.temp_c

    # Create a function for PID controller
    def PID(self):

        # Define gain constants and reference value (temperature)
        self.Kp = 1   # Proportional gain
        self.Ki = 0   # Integral gain
        self.Kd = 0  # Differential gain
        self.ref_val = self.T   # Reference value

        # Calculations
        self.mes_val = self.temp_c
        self.curr_error = self.ref_val - self.mes_val # Calculate error
        self.delta_error = self.curr_error - self.prev_error # Change in error
        self.delta_time = 5 # Time elapsed

        self.P = self.Kp * self.curr_error # Calculate proportional term
        self.I += self.Ki * (self.curr_error * self.delta_time) # Calculate integral term
        self.D = self.Kd * (self.delta_error / self.delta_time) # Calculate differential term
        self.U = self.P + self.I + self.D # Output
        self.prev_error = self.curr_error # Reset

        # Negative PID Control
       	if (self.U >= 5) & (self.U < 95):
            self.dc = self.U

        elif self.U < 5:
            self.dc = 0

        elif self.U >= 95:
            self.dc = 100

        return self.U, self.dc, self.prev_error, self.curr_error, self.P, self.I, self.D

    # Creating a function to store data
    def Data(self):
        self.temp.append(self.temp_c)
        self.fw.writerow([self.ref_val, self.temp_c, self.P, self.I, self.D, self.U, self.dc])

    def Plot(self):
        plt.plot(self.temp)
        plt.show()

Start = HotPi() # Start