"""
USSM - Ultra-Simple Stock Monitor

Small afternoon-project'ish Python script that monitors a list of stock quotes. Displays 5y,2y and 3mo price history,
auto-circles over all quotes every XX seconds, downloads the data from YAHOO every hour. Uses the tkinter (Tk interface),
Matplotlib and the yahooquery package, which have to be installed. Configuration at the top of the script itself.

https://github.com/imifos/us-stockmonitor
by @imifos
05/2020
GPL3
"""
import tkinter as tk
import matplotlib.pyplot as plt
from yahooquery import Ticker
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime

AUTO_UPDATE_TIMER = 10

#
#
#
class StockSymbolTable(tk.Frame):
    """ Data table displaying list of stock and its values.
    https://stackoverflow.com/questions/11047803/creating-a-table-look-a-like-tkinter/11049650#11049650
    """

    def __init__(self, parent, rows):
        columns=3
        tk.Frame.__init__(self, parent, background="gray")
        self._widgets = []
        for row in range(rows):
            current_row = []
            for column in range(columns):
                w = 8
                f='Helvetica 12'
                c = "left_side"
                if column==0: f+=' bold'
                if column==0: c="center_ptr"
                if column==1: w=20
                label = tk.Label(self, fg="black",bg="white",text="", borderwidth=0, width=w,font=f,cursor=c)
                label.grid(row=row, column=column, sticky="nsew", padx=1, pady=1)
                current_row.append(label)
            self._widgets.append(current_row)

        for column in range(columns):
            self.grid_columnconfigure(column, weight=1)

    def bind_click(self, column, row, handler):
        widget = self._widgets[row][column]
        widget.bind("<Button-1>", handler)
        return self

    def set(self, column, row, value):
        widget = self._widgets[row][column]
        widget.configure(text=value)
        return self


#
#
#
class DataModel:
    """ Handles all aspects of stock data, including caching and querying the YAHOO web service. """

    data_cache_time={}
    data_df2y_cache={}
    data_df5y_cache ={}
    data_df3m_cache ={}
    data_price_cache ={}
    short_name_cache={}

    def get_ticker_data(self, symbol):
        """Returns the stock symbol ticker data, either from YAHOO or from local cache."""
        now = datetime.datetime.now()
        x=self.data_df2y_cache.get(symbol, None)
        cache_time=self.data_cache_time.get(symbol,99)
        if cache_time!=now.hour or x is None:

            print("download")
            self.data_cache_time[symbol]=now.hour

            t = Ticker(symbol, formatted=True)
            valid=t.validation[list(t.validation)[0]]
            if valid:
                df2y = t.history(period='2y', interval='1d')
                df5y = t.history(period='5y', interval='5d')
                df3m = t.history(period='3mo', interval='1d')
                price = float(t.price[list(t.price)[0]]['regularMarketPrice']['fmt'])
                short_name = t.quote_type[list(t.quote_type)[0]]['shortName']
            else:
                df2y=None
                df5y=None
                df3m=None
                price=0
                short_name="Unknown Ticker"

            self.data_df2y_cache[symbol]=df2y
            self.data_df5y_cache[symbol]=df5y
            self.data_df3m_cache[symbol]=df3m
            self.data_price_cache[symbol]=price
            self.short_name_cache[symbol] = short_name
        else:
            df2y = self.data_df2y_cache.get(symbol)
            df5y = self.data_df5y_cache.get(symbol)
            df3m = self.data_df3m_cache.get(symbol)
            price = self.data_price_cache.get(symbol)
            print("cache")

        return float(price), df3m, df5y, df2y

    def get_short_name(self,symbol):
        """Returns the name of the company by its ticker name, if already downloaded. The ticker name gets downloaded
        with it stock history data, so it's coming in deferred. """
        return self.short_name_cache.get(symbol, "")

    def get_price(self, symbol):
        """Returns the price of the share by its ticker name, if already downloaded. The price gets downloaded
        with it stock history data, so it's coming in deferred. """
        return self.data_price_cache.get(symbol,0)



#
#
#
class App(tk.Tk):
    """ Main Application. """

    skip_next_update_timer_update: int
    current_symbol_index: int

    INTERVAL = 15000
    TICKERS = None
    DATA = DataModel()

    def __init__(self,tickers):
        "Setup"
        tk.Tk.__init__(self)

        self.TICKERS = tickers

        global AUTO_UPDATE_TIMER
        self.INTERVAL = AUTO_UPDATE_TIMER * 1000

        self.datatable = StockSymbolTable(self, len(self.TICKERS))
        self.datatable.pack(side=tk.LEFT, anchor=tk.NW)

        for index,c in enumerate(self.TICKERS):
            self.datatable.set(0, index, c).bind_click(0, index, self.on_table_click)
            self.datatable.bind_click(1, index, self.on_table_click)

        self.skip_next_update_timer_update = 0
        self.current_symbol_index = 0
        self.graph_canvas = None
        self.update_graph()

        self.configure(background='white')
        self.title("USSM - Ultra-Simple Stock Monitor")
        self.geometry("1500x1000")
        self.after(self.INTERVAL, self.timer_signal)

    def on_table_click(self, event):
        """Click on stock symbol in table to display selected graph. """
        click_text = event.widget.cget("text")
        for ndx,symbol in enumerate(self.TICKERS):
            if symbol == click_text:
                if ndx != self.current_symbol_index:
                    self.current_symbol_index = ndx
                    self.update_graph()
                    self.skip_next_update_timer_update = 5 # suspend auto-advance for a few intervals
                    break

    def on_graph_click(self, event):
        """Click on stock graph. """
        self.skip_next_update_timer_update = 5 # suspend auto-advance for a few intervals

    def timer_signal(self):
        """Auto-advance forward timer signal received. """
        if self.skip_next_update_timer_update>0:
            self.skip_next_update_timer_update-=1
        else:
            self.current_symbol_index += 1
            if self.current_symbol_index >= len(self.TICKERS):
                self.current_symbol_index = 0
            self.update_graph()
        self.after(self.INTERVAL, self.timer_signal)


    def update_graph(self):
        """ Replace current graph with new one specified by the current symbol index. """
        tmp_canvas = self.build_plot_canvas()
        if self.graph_canvas:
            # Closing the figure to remove it from the internal matlibplot state machine, so it can be garbage collected
            plt.close(self.graph_canvas.figure)
            self.graph_canvas.get_tk_widget().destroy()

        self.graph_canvas=tmp_canvas
        self.graph_canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.graph_canvas.get_tk_widget().bind("<Button-1>", self.on_graph_click)

        # Company names are filled with data fetched over time. Stock price updated over time. Updated these values.
        self.datatable.set(1, self.current_symbol_index, self.DATA.get_short_name(self.get_current_symbol()))
        self.datatable.set(2, self.current_symbol_index, self.DATA.get_price(self.get_current_symbol()))

    def get_current_symbol(self):
        ""
        return self.TICKERS[self.current_symbol_index]

    def build_plot_canvas(self):
        """Gets stock data from the data manager and constructs a TKINTER canvas with plot. """

        fig = plt.figure(figsize=(10, 10), dpi=100)
        canvas=FigureCanvasTkAgg(fig, master=self)

        price,df3m,df5y,df2y = self.DATA.get_ticker_data(self.get_current_symbol())
        if df3m is None:
            return canvas

        # Overlay the 3 graphs in one Figure
        ax1 = fig.add_subplot(111, label="2y")
        ax1.plot(df2y['high'], color='darkgreen', linewidth=1)
        ax1.set_xlabel("2 Years", color="darkgreen", fontsize=8)
        ax1.xaxis.set_label_coords(0.2, 1.015)
        #ax1.yaxis.set_visible(False)
        ax1.set_title(self.get_current_symbol()+" - "+self.DATA.get_short_name(self.get_current_symbol()))
        ax1.axhline(y=price,linewidth=1, color='darkgreen',linestyle=':')
        ax1.margins(0.01)

        ax1.text(0.5, 0.5, price, transform=ax1.transAxes, fontsize=40, color='lightgray', alpha=0.7, ha='center',
                 va='center', rotation='0')

        ax2 = fig.add_subplot(111, label="5y", frame_on=False)
        ax2.plot(df5y['high'], color='peachpuff', linestyle=':')
        ax2.set_xlabel("5 Years", color="peachpuff", fontsize=8)
        ax2.xaxis.set_label_coords(0.15, 1.015)
        ax2.margins(0.01)

        ax3 = fig.add_subplot(111, label="3mo", frame_on=False)
        ax3.plot(df3m['high'], color='skyblue', linewidth=1, linestyle=':')
        ax3.set_xlabel("3 Months", color="skyblue", fontsize=8)
        ax3.xaxis.set_label_coords(0.1, 1.015)
        #ax3.xaxis.set_ticks_position('none')
        ax3.margins(0.01)

        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=-90, fontsize=6, color='skyblue')
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=-90, fontsize=6, color='peachpuff')
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=-90, fontsize=9, color='darkgreen')
        plt.setp(ax3.yaxis.get_majorticklabels(),  fontsize=6, color='skyblue')
        plt.setp(ax2.yaxis.get_majorticklabels(),  fontsize=6, color='peachpuff')
        plt.setp(ax1.yaxis.get_majorticklabels(), fontsize=9, color='darkgreen')
        #plt.autoscale(tight=True)

        return canvas

#
#
#
if __name__ == "__main__":

    import sys

    if len(sys.argv)<2:
        print("Please pass a file. 1 stock ticker symbol per line.")
        exit(-1)

    tickers=[]
    with open(sys.argv[1]) as fp:
        line = fp.readline()
        while line:
            tickers.append(line.rstrip('\r\n'))
            line = fp.readline()

    app = App(tickers)
    app.mainloop()
