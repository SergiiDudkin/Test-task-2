#!/usr/bin/env python
import requests
import platform
import math
import re
try: # Python 2
    from Tkinter import *
    import tkMessageBox
except: # Python 3
    from tkinter import *
    import tkinter.messagebox


def sci_round(num, sig_fig=1, ndigits=1e6):
    """Round with precision sig_fig and max digits after coma ndigits"""
    return 0.0 if not num else round(num, min(sig_fig - int(math.floor(math.log10(abs(num) / 2.0))) - 1, ndigits))


class EntryValid(Entry, object):
    """General entry widget with validation. Callback function must be added as the 2nd argument."""
    def __init__(self, parent, callback, **kwargs):
        self.callback = callback
        self.strvar = StringVar()
        self.strvar.trace('w', self.entry_callback)
        kwargs['textvariable'] = self.strvar
        super(EntryValid, self).__init__(parent, **kwargs)
        self.entry_callback()

    def entry_callback(self, *args):
        """This method is called every time when user enters something"""
        self['bg'] = 'lemon chiffon' if self.validate() else '#fca7b8' # Set color of the entry field
        self.callback(self.strvar.get())

    def validate(self):
        """This validator is used solely for indication"""
        return re.match(r'^ *\d*\.?\d* *$', self.strvar.get()) is not None


class CurrencyTableRaw(object):
    """Frame with 'Ok' and 'Cancel' buttons"""
    def __init__(self, parent, currency, row, column):
        self.currency = currency

        self.lbl_amnt = Label(parent, width=11, bg='white', relief=SUNKEN)
        self.lbl_amnt.grid(row=row, column=column, padx=2, pady=2)

        Label(parent, text=currency).grid(row=row, column=column+1, padx=2, pady=2)

        self.lbl_rate = Label(parent, width=10, bg='white', relief=SUNKEN)
        self.lbl_rate.grid(row=row, column=column+2, padx=2, pady=2)

    def update_rate(self, rate):
        """Set new exchange rate"""
        self.rate = rate
        self.lbl_rate['text'] = rate

    def update_amnt(self, amnt_uah):
        """Convert UAH and set amount of the given currency"""
        if amnt_uah is not None and hasattr(self, 'rate') and self.rate != 0:
            rounded = sci_round(amnt_uah / self.rate, 6, 5) # Round
            self.lbl_amnt['text'] = rounded if rounded < 10e8 else '{:.5E}'.format(rounded) # Use scientific notation in case of very big numbers
        else: self.lbl_amnt['text'] = ''


class App(Tk, object):
    """Application with GUI"""
    def __init__(self, currencies):
        super(App, self).__init__()

        # Window setup
        self.title('NBU Exchange Rates')
        op_sys = platform.system()
        try: # Add window logo
            if op_sys == 'Linux': self.tk.call('wm', 'iconphoto', self._w, PhotoImage(file='logo-m.png'))
            elif op_sys == 'Windows': self.iconbitmap('logo-m.png')
        except: pass
        self.resizable(True, True)

        # Create widgets
            # Footer
        frm_btm = Frame(self) # Bottom frame
        frm_btm.pack(side=BOTTOM, fill=X)
        Label(frm_btm, text='Exchange date:').pack(side=LEFT, padx=2, pady=2)
        self.lbl_date = Label(frm_btm)
        self.lbl_date.pack(side=LEFT, padx=2, pady=2)
        Button(frm_btm, text='Update', command=self.update_rates, width=6).pack(side=RIGHT, padx=2, pady=2)

            # Table
        frm_tbl = Frame(self) # Frame with table
        frm_tbl.pack(side=TOP, padx=2, pady=2, fill=X)

                # Table header
        Label(frm_tbl, text='Amount, UAH', font=('Arial', 10, 'bold')).grid(row=0, column=0, padx=2, pady=2)
        Label(frm_tbl, text='Converted', font=('Arial', 10, 'bold')).grid(row=0, column=2, padx=2, pady=2)
        Label(frm_tbl, text='Currency', font=('Arial', 10, 'bold'), width=10).grid(row=0, column=3, padx=2, pady=2)
        Label(frm_tbl, text='Rates', font=('Arial', 10, 'bold'), width=10).grid(row=0, column=4, padx=2, pady=2)

                # Table body
        rowspan = max(1, len(currencies))
        Label(frm_tbl, text=u'\u21E8', font=('Arial', 18)).grid(row=1, column=1, rowspan=rowspan, padx=2, pady=2)
        self.cbars = [CurrencyTableRaw(frm_tbl, currency, idx + 1, 2) for idx, currency in enumerate(currencies)] # Add rows to the table
        self.entr_uah = EntryValid(frm_tbl, self.update_amnts, width=10)
        self.entr_uah.grid(row=1, column=0, rowspan=rowspan, padx=2, pady=2) # Entry widget for UAH

        for idx, weight in enumerate([1, 1, 1, 10, 1]): frm_tbl.grid_columnconfigure(idx, weight=weight)

        self.update_rates()

    def update_rates(self):
        """Make http request and update all exchange rates"""
        try:
            response = requests.get('https://bank.gov.ua/NBUStatService/v1/statdirectory/exchangenew?json')
            response.raise_for_status()
        except:
            tkMessageBox.showwarning('ERROR', 'bank.gov.ua is not available.\nCannot connect to the server.')
            return

        self.data = response.json()
        cc_list = [item['cc'] for item in self.data]
        for cbar in self.cbars:
            idx = cc_list.index(cbar.currency)
            cbar.update_rate(self.data[idx]['rate'])

        # Update exchange date
        self.lbl_date['text'] = self.data[0]['exchangedate']
        self.lbl_date['fg'] = 'blue'
        self.after(1000, self.date_in_black)

        # Update amounts
        self.update_amnts(self.entr_uah.strvar.get())

    def update_amnts(self, strvar):
        """Convert UAH to other currencies"""
        try: amnt_uah = float(strvar)
        except: amnt_uah = None
        if amnt_uah is not None and not 0 <= amnt_uah < 1e80: amnt_uah = None
        for cbar in self.cbars: cbar.update_amnt(amnt_uah)

    def date_in_black(self):
        """Paint exchange date in black"""
        self.lbl_date['fg'] = 'black'


if __name__ == '__main__':
    # Settings
    currencies = ('USD', 'EUR', 'CNY', 'RUB', 'JPY', 'CHF')

    gui = App(currencies)
    gui.mainloop()
