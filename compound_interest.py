""" module to calculate coumpund interest rates with consideration of minimum interest """
from math import log10
#import json
from datetime import datetime
import pandas as pd

class CompoundInterest:
    """ Calculates Compound Interests and Interest Totals stored in a csv file.
        Based upon a new principal value for each year termed investment block and a separate
        minimum interest for each separate investment block compound interests are calculated
        and stored in a data frame.
        For each calculated year it will be evaluated whether the current interest per year or the
        minimum interest (="Garantiezins"/"guaranteed interest") for each investment
        block is higher and the highest interest will be used for interest calculation.
        It's easiest to check calculation with accompanied csv file
    """

    def __init__(self, fp: str, year_min: int, year_max: int,
                 fp_save=None, fp_save_json=None, debug=False,
                 colname_index="YEAR", colname_amount="AMOUNT",
                 colname_min_interest="MIN_INTEREST", colname_interest="INTEREST",
                 decimal_sign=",", delimiter=";"):
        """ Constructor"""
        self.year_min = year_min
        self.year_max = year_max
        self.debug = debug
        self.colname_index = colname_index
        self.colname_amount = colname_amount
        self.colname_interest = colname_interest
        self.colname_min_interest = colname_min_interest
        self.data_cols = [colname_amount, colname_interest, colname_min_interest]
        self.fp = fp
        self.fp_save = fp_save
        self.decimal_sign = decimal_sign
        self.delimiter = delimiter
        self.df_original = None
        self.df_summary = None
        self.calculated = False
        self.fp_save_json = fp_save_json
        # read data
        self.read_csv()
        self.df = self.df_original.copy()

    def read_csv(self):
        """ reads the raw data from csv and puts it into """
        data = pd.read_csv(self.fp, header=0, decimal=self.decimal_sign, delimiter=self.delimiter)
        data.set_index(self.colname_index, inplace=True)
        self.df_original = pd.DataFrame(data, columns=self.data_cols)

    def to_csv(self):
        """ saves summary data to csv """
        if self.fp_save is None:
            return

        if self.df_summary is None:
            self.get_summary()

        self.df_summary["df"].to_csv(path_or_buf=self.fp_save,
                                     sep=self.delimiter, decimal=self.decimal_sign)

    def to_json(self):
        """ saves data to json """
        if self.fp_save_json is None:
            return
        # todo implement json conversion

    def sum_frame_by_column(self):
        """ calculates totals of values in separate column list """
        if self.df is None:
            return
        cols = list(range(self.year_min, self.year_max+1))
        self.df["TOTAL"] = self.df[cols].astype(float).sum(axis=1)

    def get_compound_interest_sum(self, year):
        """ calculates compound interests and total sum for investment block
            assigned to given year"""
        if year > self.year_max:
            return
        minimum_interest = self.df.loc[year][self.colname_min_interest]
        amount = self.df.loc[year][self.colname_amount]
        for y in range(year, self.year_max+1):
            current_interest = self.df.loc[y][self.colname_interest]
            interest = max(current_interest, minimum_interest)
            if self.debug:
                print(f"Year {y} Amount {amount:.0f} "+
                      f" interest:{current_interest:.1%} =>"+
                      f" interest {interest:.1%} ({(amount*interest):.0f})")
            self.df[year][y] = amount
            amount = amount*(1+interest)

    def calculate_annual_compound_totals(self):
        """ calculates new totals and compund interest for each investment block """
        for y in range(self.year_min, self.year_max+1):
            # create a new column for a given investment block
            self.df[y] = 0.
            amount = self.df.loc[y][self.colname_amount]
            min_interest = self.df.loc[y][self.colname_min_interest]
            if self.debug:
                print(f"\n--- Investment Block ({y}): {amount:.0f},"+
                      f" Min.interest: {min_interest:.1%} -------")
            self.get_compound_interest_sum(y)
            if self.debug:
                final_amount = self.df.loc[self.year_max][y]
                margin = (final_amount-amount)/amount
                margin_p_year = margin / (self.year_max-y+0.00001)
                print(f"Final amount: {final_amount:.0f} profit {final_amount-amount:.0f} "+
                      f"margin {margin:.0%} avg margin {margin_p_year:.0%}")

        # Now Add the sum as new column to data frame
        self.sum_frame_by_column()
        self.calculated = True

    def get_df(self):
        """ returns the calulated interest blocks """
        if not self.calculated:
            self.calculate_annual_compound_totals()
        return self.df

    def get_summary(self, year_from=None, year_max=None):
        """ returns statistics as dictionary """
        if not self.calculated:
            self.calculate_annual_compound_totals()

        summary = {}
        # only up to year max
        df = self.df.loc[:year_max].copy()
        col_investment_block = self.colname_amount
        df[col_investment_block] = df[col_investment_block].astype(int)
        col_interest_list = []
        col_totals_list = []
        for y in range(year_from, year_max+1):
            df[y] = self.df[y].astype(int)
            col_totals_list.append(y)

        for y in range(year_from, year_max+1):
            col_interest = "I"+str(y)
            col_interest_list.append(col_interest)
            df[col_interest] = df[y].diff().fillna(0).astype(int)
            df.loc[[y], [col_interest]] = 0

        # totals for investment blocks/ interest in row
        df.loc[:, 'ITotal'] = df[col_interest_list].sum(axis=1)
        df.loc[:, 'Total'] = df[col_totals_list].sum(axis=1)

        # calculate effective interest rates for each investment block
        df["ratio"] = 0.
        df["Ieff"] = 0.
        for y in range(year_from, year_max+1):
            initial = df[y][y]
            final = df[y][year_max]
            ratio = final / initial
            if y != year_max:
                interest_eff = 10**(log10(ratio)/(year_max-y))-1
            else:
                interest_eff = 0

            df.loc[[y], ["Ieff"]] = interest_eff
            df.loc[[y], ["ratio"]] = ratio

        # now calculate stats
        sum_investment = df.loc[:, self.colname_amount].sum()
        sum_interest = df.loc[:, "ITotal"].sum()
        total = sum_interest+sum_investment

        if year_from is None:
            # get the min value
            year_from = min(df.index.values)
        years = year_max - year_from + 1
        roi_total = sum_interest / sum_investment
        interest_average = roi_total / years
        # effective interest rate : interest rate that would have
        # gained the same capital after investment time
        capital_increase = total / sum_investment
        interest_effective = 10**(log10(capital_increase)/years)-1

        summary["created"] = datetime.now()
        summary["csv"] = self.fp
        summary["COLUMN_INDEX"] = self.colname_index
        summary["COLUMN_LIST"] = self.data_cols
        summary["year_from"] = year_from
        summary["year_max"] = year_max
        summary["years"] = years
        summary["sum_investment"] = sum_investment
        summary["sum_interest"] = sum_interest
        summary["total"] = total
        summary["roi_total"] = roi_total
        summary["interest_average"] = interest_average
        summary["interest_effective"] = interest_effective
        summary["capital_increase"] = capital_increase
        summary["df"] = df

        if self.debug:
            print(f"\n--- GET SUMMARY / STATS {year_from}-{year_max}, {years} yrs ---")
            print(f"    invest: {sum_investment}, interest: {sum_interest}, total: {total}")
            print(f"    interest average: {interest_average:.1%},"+
                  f" interest effective: {interest_effective:.1%}")

        self.df_summary = summary

        return summary
