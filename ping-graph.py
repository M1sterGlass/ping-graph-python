""" ping-graph.py: Ping latency on a graph in Python. """

__author__      = "M1sterGlass"
__copyright__   = "Copyright 2023, Planet Earth"
__version__     = "1.0.3"

import argparse
import datetime as dt
import customtkinter
import time
import logging
import matplotlib as mpl
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from pythonping import ping
from statistics import mean

# Logging
FORMAT = '%(asctime)s | %(levelname)-8s | %(message)s'
logging.basicConfig(format=FORMAT)
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(level=logging.INFO)


class ArgumentReader:
   # Init parser and adding arguments
    parser = argparse.ArgumentParser()
    
    parser.add_argument(
        "-t",
        dest='target',
        # default='1.1.1.1', type=str,
        help = "Target hostname or IP address, default is [1.1.1.1]"
    )
    
    parser.add_argument(
        "-s",
        dest='seconds',
        default=60, type=int,
        help = "Number of seconds to display, default is [60] seconds"
    )
    parser.add_argument(
        "-i",
        dest='interval',
        default=200, type=int,
        help = "Ping interval in milli-seconds, default is [200] ms"
    )
    
    parser.add_argument(
        "-v",
        action='version',
        version='%(prog)s {version}'.format(version=__version__),
        help = "Show version"
    )
    
    # Read arguments from commandline
    arguments = parser.parse_args()

    if not arguments.target:
        LOGGER.debug(f'gui_mode true')
        gui_mode = True
    else:
        LOGGER.debug(f'gui_mode false')
        gui_mode = False


class Gui(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        # Custom Tkinter
        customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
        customtkinter.set_default_color_theme("green")  # Themes: "blue" (standard), "green", "dark-blue"

        # configure window
        self.title("Ping Graph")
        self.geometry(f"{600}x{800}")
        
        # Frame
        self.frame = customtkinter.CTkFrame(master=self)
        self.frame.pack(padx=20, pady=40, fill="both", expand=True)

        self.label = customtkinter.CTkLabel(
            master=self.frame,
            text="Ping Graph",
            font=("Roboto", 24)
            )
        self.label.pack(padx=0, pady=(20,20))

        self.target_label = customtkinter.CTkLabel(
            master=self.frame,
            text="Target (Hostname or IP address)",
            font=("Roboto", 12)
            )
        self.target_label.pack(padx=0, pady=0)

        self.target_entry = customtkinter.CTkEntry(
            master=self.frame,
            placeholder_text="Target"
            )
        self.target_entry.insert(0, "1.1.1.1")
        self.target_entry.pack(padx=0, pady=(0,20))

        self.seconds_label = customtkinter.CTkLabel(
            master=self.frame,
            text="Time (seconds)",
            font=("Roboto", 12)
            )
        self.seconds_label.pack(padx=0, pady=0)

        self.seconds_entry = customtkinter.CTkEntry(
            master=self.frame,
            placeholder_text="Seconds"
            )
        self.seconds_entry.insert(0, "30")
        self.seconds_entry.pack(padx=0, pady=(0,20))

        self.interval_label = customtkinter.CTkLabel(
            master=self.frame,
            text="Interval (milli-seconds)",
            font=("Roboto", 12)
            )
        self.interval_label.pack(padx=0, pady=0)

        self.interval_entry = customtkinter.CTkEntry(
            master=self.frame,
            placeholder_text="Interval (ms)"
            )
        self.interval_entry.insert(0, "200")
        self.interval_entry.pack(padx=0, pady=(0,20))

        self.button = customtkinter.CTkButton(
            master=self.frame,
            text="Execute",
            command=self.button_event
            )
        self.button.pack(padx=0, pady=(20,20))

        self.console_label = customtkinter.CTkLabel(
            master=self.frame,
            text="Console",
            font=("Roboto", 12)
            )
        self.console_label.pack(padx=0, pady=(20,0))
        
        self.console_textbox = customtkinter.CTkTextbox(
            master=self.frame,
            font=('arial',12 ,'bold'),
            width=600,
            height=800
            )
        self.console_textbox.configure(state="disabled") 
        self.console_textbox.pack()

        # checkbox = customtkinter.CTkCheckBox(master=frame, text="Max runtime")
        # checkbox.pack(padx=10, pady=10)
 
    def print_message(self, message: str):
        self.message = message
        
        if ar.gui_mode is True:
            self.console_textbox.configure(state="normal")
            self.console_textbox.insert(0.0, self.message + "\n")
            self.console_textbox.configure(state="disabled") 
        else:
            print(self.message)

    def button_event(self):
        self.ping_target = str(self.target_entry.get())
        self.ping_seconds = int(self.seconds_entry.get())
        self.ping_interval = int(self.interval_entry.get())
        self.print_message(f'Target: {self.ping_target} -- Time: {self.ping_seconds} sec -- Interval: {self.ping_interval} ms')

        pinger = Pinger(self.ping_target)
        plotter = Plotter(pinger, seconds=self.ping_seconds, interval=self.ping_interval)
        plotter.start()

    def start(self):
        self.mainloop()


class Pinger:
    TIMEOUT = 2000  # 2000 default timeout (in ms)

    def __init__(self, host: str, timeout: int = TIMEOUT):
        self.host = host
        self.timeout = timeout

    def call(self) -> float:
        try:
            resp = ping(self.host, count=1, timeout=self.timeout/1000)
            rtt = resp.rtt_avg_ms
        except Exception as e:
            rtt = self.timeout

        # if timeout change rtt to 0
        if rtt >= self.timeout:
            rtt = 0
        return rtt


class Plotter:
    # Defaults
    SECONDS = 30
    INTERVAL = 200
    MAXPOINTS = 150

    # Matplotlib Graph configuration
    DARK_COLOR = 'black'
    MEDIUM_COLOR = 'grey'
    LIGHT_COLOR = 'white'
    PRIMARY_COLOR = 'green'
    SECONDARY_COLOR = 'white'
    PRI_LINE_FORMAT = '+-'
    SEC_LINE_FORMAT = ':'
    mpl.rcParams['toolbar'] = 'None'
    mpl.rcParams['figure.figsize'] = [10.0, 5.5]
    mpl.rcParams['font.size'] = '10'
    mpl.rcParams['figure.facecolor'] = DARK_COLOR
    mpl.rcParams['text.color'] = LIGHT_COLOR
    mpl.rcParams['axes.facecolor'] = DARK_COLOR
    mpl.rcParams['axes.labelcolor'] = LIGHT_COLOR
    mpl.rcParams['xtick.color'] = LIGHT_COLOR
    mpl.rcParams['ytick.color'] = LIGHT_COLOR
    mpl.rcParams['grid.color'] = MEDIUM_COLOR
    mpl.rcParams['axes.grid'] = True
    mpl.rcParams['grid.linestyle'] = ':'
    mpl.rcParams['grid.linewidth'] = '0.5'
    mpl.rcParams['lines.linewidth'] = '1'
    mpl.rcParams['legend.loc'] = 'upper left'

    def __init__(self, pinger: Pinger, seconds: int = SECONDS, interval: int = INTERVAL):
        self.pinger = pinger
        self.seconds = seconds
        self.interval = interval
        self.maxpoints = self.MAXPOINTS #int(seconds / (interval / 1000))
        self.timestamps = []
        self.rtts = []
        self.rtts_avg = []
        self.rtts_seconds = 0
        self.rtts_lost = 0
        self.first_run = True
        self.fig, self.ax = plt.subplots()

    def wait_for_first_connection(self) -> None:
        # Retry pinger if first run is a timeout
        if self.first_run is True:
            while self.rtt == 0:
                LOGGER.warning("Waiting for connection...")
                time.sleep(1)
                self.rtt = self.pinger.call()
            LOGGER.info("Connection ok")
            self.first_run = False

    def append_list(self, listname, value) -> list:
        result = listname.append(value)
        result = listname[-self.maxpoints:]
        return result
    
    def calculate_maxpoints(self) -> int:
        self.rtts_seconds = (self.timestamps[-1] - self.timestamps[0]).total_seconds()
        LOGGER.debug(f'run {self.rtts_seconds:.2f} sec {self.seconds:.2f} max {self.maxpoints}')

        # if graph seconds less then argument seconds
        if self.rtts_seconds < self.seconds:
            LOGGER.debug(f'maxpoints adding')
            return len(self.rtts) + 1
        
        if self.seconds <= self.rtts_seconds <= self.seconds + 1:
            LOGGER.debug(f'maxpoints do nothing')
            return len(self.rtts)
       
        # if graph seconds exceeds argument seconds+1 
        if self.rtts_seconds > self.seconds + 1:
            if len(self.rtts) > self.seconds / 2:
                LOGGER.debug(f'maxpoints subtract')
                return len(self.rtts) - 1

    def update_data(self):
        # Ping target
        self.rtt = self.pinger.call()
        self.wait_for_first_connection()

        # Add timestamp to list
        self.timestamps = self.append_list(self.timestamps, dt.datetime.now())
        
        # Add rtt to list
        self.rtts = self.append_list(self.rtts, self.rtt)

        # Timeouts
        self.rtts_lost = self.rtts.count(0)
        self.rtts_lost_pct = (self.rtts_lost / len(self.rtts)) * 100

        # Average from rtts list, excluding timeouts where rtt=0
        if sum(self.rtts) > 0:
            # Minimum, maximum, average
            self.rtt_min = min(list(filter(lambda x: x != 0, self.rtts)))
            self.rtt_max = max(self.rtts)
            self.rtt_avg = mean(list(filter(lambda x: x != 0, self.rtts)))
        else: 
            LOGGER.info(f'Connection timeout')

        # Add rtt_avg to list
        self.rtts_avg = self.append_list(self.rtts_avg, self.rtt_avg)
        
        # Calculate number of maxpoints
        self.maxpoints = self.calculate_maxpoints()

        LOGGER.debug(f'''
            rtt {self.rtt:.2f}
            min {self.rtt_min:.2f}
            max {self.rtt_max:.2f}
            avg {self.rtt_avg:.2f}
            tos {self.rtts_lost:.2f}
            pts {self.maxpoints}
        ''')

    def render_frame(self, i: int):
        self.update_data()
        # Plot clear
        self.ax.clear()

        # Plot rtts
        self.ax.plot_date(
            self.timestamps,
            self.rtts,
            fmt = self.PRI_LINE_FORMAT,
            color = self.PRIMARY_COLOR,
            label = self.pinger.host
        )
        
        # Plot averages
        self.ax.plot_date(
            self.timestamps,
            self.rtts_avg,
            fmt = self.SEC_LINE_FORMAT,
            color = self.SECONDARY_COLOR,
            label = "Average"
        )

        # Plot texts
        plt.suptitle(f'Min: {self.rtt_min:.0f}ms  Max: {self.rtt_max:.0f}ms  Avg: {self.rtt_avg:.0f}ms  Lost: {self.rtts_lost} ({self.rtts_lost_pct:.0f}% loss) ')
        plt.title(f'( {self.rtts_seconds:.2f} seconds / {self.maxpoints} points ) ')
        plt.ylabel(f'Round trip time (milli-seconds)')
        plt.legend([self.pinger.host, 'Average'])

    def stop(self, event_object):
        LOGGER.info(f'Stopped')
        plt.close('all')

    def start(self):
        LOGGER.info(f'Started')
        # Assign to variable to avoid garbage collection.
        anim = animation.FuncAnimation(
            fig=self.fig,
            func=self.render_frame,
            interval=self.interval
        )
        # Close all plots on exit
        self.fig.canvas.mpl_connect("close_event", self.stop)
        plt.show()


if __name__ == "__main__":
    ar = ArgumentReader()

    if ar.gui_mode is True:
        gui = Gui()
        gui.start()
    else:
        pinger = Pinger(ar.arguments.target)
        plotter = Plotter(pinger, seconds=ar.arguments.seconds, interval=ar.arguments.interval)
        plotter.start()   
