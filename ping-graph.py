""" ping-graph.py: Ping latency on a graph in Python. """

__author__      = "M1sterGlass"
__copyright__   = "Copyright 2023, Planet Earth"
__version__     = "1.0.0"

import argparse
import datetime as dt
import matplotlib as mpl
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from pythonping import ping
from statistics import mean

# Graph configuration
DARK_COLOR = 'black'
MEDIUM_COLOR = 'grey'
LIGHT_COLOR = 'white'
PRI_COLOR = 'green'
SEC_COLOR = 'white'
PRI_LINE_FORMAT = '+-'
SEC_LINE_FORMAT = ':'
mpl.rcParams['toolbar'] = 'None'
mpl.rcParams['figure.figsize'] = [10.0, 5.5]
mpl.rcParams['font.size'] = '8'
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

        return rtt

class PingPlotter:
    # Defaults
    MAXPOINTS = 1000
    INTERVAL = 500

    def __init__(self, pinger: Pinger, maxpoints: int = MAXPOINTS, interval: int = INTERVAL):
        self.pinger = pinger
        self.maxpoints = maxpoints
        self.interval = interval
        # Init data points

        self.timestamps = []
        self.rtts = []
        self.rtts_avg = []

        # Init plot
        self.fig, self.ax = plt.subplots()
  
   
    def __update_data(self):
        rtt = self.pinger.call()

        # Timestamps
        self.timestamps.append(dt.datetime.now())
        self.timestamps = self.timestamps[-self.maxpoints:]

        # RTT, if timeout, replace rtt with 1
        if rtt >= self.pinger.TIMEOUT:
            rtt = 1
        self.rtts.append(rtt)
        self.rtts = self.rtts[-self.maxpoints:]

        # Average from rtts list, excluding timeouts where rtt=1 
        self.rtt_current_avg = round(mean(list(filter(lambda num: num != 1, self.rtts))), 2)
        self.rtts_avg.append(self.rtt_current_avg)
        self.rtts_avg = self.rtts_avg[-self.maxpoints:]

        # Runtime is seconds
        self.rtts_seconds = self.interval * len(self.rtts) / 1000

        # Number of timeouts
        self.rtts_timeouts = self.rtts.count(1)

        # print(f'''{
        #     self.timestamps[-1]} \t
        #     rtt : {rtt} \t
        #     avg : {self.rtt_current_avg} \t
        #     to  : {self.rtts_timeouts}'''
        # )


    def __render_frame(self, i: int):
        self.__update_data()
        # Clear
        self.ax.clear()

        # Plot rtts
        self.ax.plot_date(
            self.timestamps,
            self.rtts,
            fmt=PRI_LINE_FORMAT,
            color = PRI_COLOR,
            label = self.pinger.host
            )
        # Plot average
        self.ax.plot_date(
            self.timestamps,
            self.rtts_avg,
            fmt=SEC_LINE_FORMAT,
            color = SEC_COLOR,
            label = "Average"
            )

        # Plot texts
        main_title = f'[ Average {self.rtt_current_avg:.2f} ms ] [ Request timeouts {self.rtts_timeouts} ]'
        plt.suptitle(main_title)
        sub_title = f'({self.rtts_seconds:.2f} seconds)'
        plt.title((sub_title))
        plt.ylabel('Round trip (milli-seconds)')
        plt.legend([self.pinger.host, 'Average'])


    def start(self):
        # Assign to variable to avoid garbage collection.
        a = animation.FuncAnimation(
            fig=self.fig,
            func=self.__render_frame,
            interval=self.interval
            )
        plt.show()


if __name__ == "__main__":
    # Init parser and adding optional arguments
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-t", dest='target', default='1.1.1.1', type=str,
        help = "Target hostname or IP address, default is [1.1.1.1]"
        )
    parser.add_argument(
        "-s", dest='seconds', default=60, type=int,
        help = "Number of seconds to display, default is [60] seconds"
        )
    parser.add_argument(
        "-i", dest='interval', default=200, type=int,
        help = "Ping interval in milli-seconds, default is [200] ms"
        )
    parser.add_argument(
        "-v", action='version', version='%(prog)s {version}'.format(version=__version__),
        help = "Show version"
        )

   # Read arguments from command line
    args = parser.parse_args()
    if args.target:
        print(f'''Target: \t {args.target}''')
        ping_target = args.target
    if args.seconds:
        print(f'''Seconds: \t {args.seconds}''')
        ping_seconds = args.seconds
    if args.interval:
        print(f'''Interval: \t {args.interval}''')
        ping_interval = args.interval

    # calculate maximum plot points
    ping_maxpoints = int(ping_seconds * 1000 / ping_interval)

    # Run
    pinger = Pinger(ping_target)
    plotter = PingPlotter(pinger, maxpoints=ping_maxpoints, interval=ping_interval)
    plotter.start()

