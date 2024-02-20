import pandas as pd
import numpy as np
import plotly.graph_objects as go


class Waterfall(object):
    def __init__(
            self, df: pd.DataFrame, x:str, y:str, group:str|None=None, category:str|None=None, 
            barwidth:float=0.3, gap:float=0.01, connector_line:dict=dict(color="darkgrey", width=.75),
            colors:dict|None=None, total:bool=False, total_type:str="category", total_column_name:str="Total",
            subtotals:dict|None=None, 
       ):
        """Instanciate Waterfall object. All configuration is done by handing the correct kwargs. 

        Args:
            df (pd.DataFrame): Pandas Dataframe containing all data in correct format. 
            x (str): Column containing x-values/labels
            y (str): Column containing y-values
            group (str | None, optional): If not None: column containing group labels. Defaults to None.
            category (str | None, optional): If not None: column containing category labels. Defaults to None.
            barwidth (float, optional): Width of bars, should be 0.0 to 1.0. Defaults to 0.3.
            gap (float, optional): Gap between bars of different groups. Defaults to 0.01.
            connector_line (dict, optional): Parameters defining line style for lines connecting bars. Defaults to dict(color="darkgrey", width=.75).
            colors (dict | None, optional): dict identifying colors, compare documentation / example. Defaults to None, which uses default colors. 
            total (bool, optional): If True, calculates the total and ads it as last x-value. Defaults to False.
            total_type (str, optional): How to calculate the total. Can be "category" or "sumtotal". Defaults to "category".
            total_column_name (str, optional): Label of the x-value for total . Defaults to "Total".
            subtotals (dict | None, optional): dict with subtotals which should be added in format {"where": "label_name"}. Defaults to None.
        """
         
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Expected df to be of type DataFrame")
        self._df = df
        self._x = x
        self._y = y
        self._group = group
        self._category = category 
        self._barwidth = barwidth
        self._gap = gap
        self._connector_line = connector_line
        self._colors = colors
        self._total_column_name = total_column_name
        self._test_df()
        if subtotals is None:
            self._subtotals = {}
        elif isinstance(subtotals, dict):
            self._subtotals = subtotals
        else:
            raise TypeError("subtotals should be of type dict")
        self._total = total
        self._total_type = total_type
        if total and (total_type=="category"):
            self._subtotals.update({self._df[self._x].unique()[-1]: total_column_name})

    
    def get_fig(self) -> go.Figure:
        """Creates Plotly Figure instance

        Raises:
            NotImplementedError: Certain features, such as mixed signs per x value are not (yet) supported

        Returns:
            Figure: Configured plotly.graph_objects.Figure instance
        """

        # tdf = self._get_df_merged_w_color()
        tdf = self._df.copy()
        X = self._get_x_values(tdf)

        fig = go.Figure()

        if self._group is None:
            self.__totalgroups = 1
            self._add_group(fig, X, 0, None, tdf)
        else:
            self.__totalgroups = len(tdf[self._group].unique())
            for groupno, (groupname, group) in enumerate(tdf.groupby(self._group, sort=False)):
                self._add_group(fig, X, groupno, groupname, group)

        # Test output for mixed sign bars
        for i in zip(*[i["y"] for i in fig.data]):
            ia = np.array(i)
            if not (np.all((ia>=0) | np.isnan(ia)) | np.all((ia<=0) | np.isnan(ia))):
                raise NotImplementedError("Currently mixed signed categories in totals are not supported (yet)")

        if self._total and (self._total_type == "sumtotal"):
            self._add_sumtotal(fig, X, tdf)
            X = pd.concat([X, pd.DataFrame({self._x: X[self._x].max()+1}, index=[self._total_column_name])])

        fig.update_layout(
            xaxis = dict(
                tickmode = 'array',
                tickvals = X[self._x],
                ticktext = X.index
            )
        )
        return fig
  
    def _test_df(self):
        if self._group is None:
            gb = self._x
        else:
            gb = [self._group, self._x]
        for i, g in self._df.groupby(gb):
            if not (np.all(g[self._y]>=0) | np.all(g[self._y]<=0)):
                raise NotImplementedError("Currently mixed signed categorization is not supported (yet)")
    
    def add_subtotal(self, x, name):
        if self._subtotals is None:
            self.add_total()
        if x not in self._df[self._x].unique():
            raise ValueError("Cannot find value {} in data".format(x))
        self._subtotals.update({x: name})

    def _get_x_values(self, tdf):
        # Define x axis and include subtotals and totals
        X = list(tdf[self._x].unique())
        mt = [False] * len(X)
        for total in self._subtotals:
            pos = X.index(total)+1
            X.insert(pos, self._subtotals[total])
            mt.insert(pos, True)
        X = pd.DataFrame({"label":X, "makeTotal": mt}).reset_index().set_index("label").rename({"index": self._x}, axis=1)
        return X

    def _add_group(self, fig, X, groupno, groupname, group):
        b = group.groupby([self._x], sort=False)[self._y].sum().cumsum().shift(1).fillna(0)
        b = X.merge(pd.DataFrame(b), left_index=True, right_index=True, how="left")[self._y].fillna(0)
        #TODO: add check for mixed signal in total group

        if isinstance(self._colors, dict) and (groupname in self._colors):
            colors = self._colors[groupname]
        else:
            colors = self._colors

        if self._category is None:
            x, y, b = self._add_bar(fig, X, b, None, group, groupno, groupname, group, colors)
        else:
            for categoryname, category in group.groupby(self._category, sort=False):
                x, y, b = self._add_bar(fig, X, b, categoryname, category, groupno, groupname, group, colors)
        self._add_lines(fig, X, group, groupno)

    def _add_bar(self, fig, X, b, categoryname, category, groupno, groupname, group, colors):
        values = category.groupby([self._x])[self._y].sum()
        x = X[self._x]
        y = X.merge(pd.DataFrame(values), left_index=True, right_index=True, how="left")[self._y]
        y = y.fillna(0).cumsum().where(X.makeTotal, y)

        if isinstance(colors, dict) and (categoryname in colors):
            colors = colors[categoryname]
        
        if categoryname is None:
            name = groupname
            groupnametitle = None
        else:
            name = categoryname
            groupnametitle = groupname
            
        
        fig.add_bar(
            x=x, y=y, base=b, offsetgroup=groupno, name=name, marker_color=colors,
            legendgroup=groupname, legendgrouptitle_text=groupnametitle,
            width=self._barwidth, offset=-(self._barwidth+self._gap/2)*self.__totalgroups/2 + 
                (self._barwidth+self._gap/2)*groupno,
            )
        b += y.fillna(0)
        return x, y, b

    def _add_lines(self, fig, X, group, groupno):
        x = X[self._x]
        ys = group.groupby([self._x], sort=False)[self._y].sum()
        ys = X.merge(pd.DataFrame(ys), left_index=True, right_index=True, how="left")[self._y].fillna(0).cumsum().ffill()
        x0s = x[0:-1]-(self._barwidth+self._gap/2)*self.__totalgroups/2 + (self._barwidth+self._gap/2)*groupno
        x1s = x[1:]-(self._barwidth+self._gap/2)*self.__totalgroups/2 + (self._barwidth+self._gap/2)*groupno + self._barwidth
        for i, (x0, x1, y) in enumerate(zip(x0s, x1s, ys)):
            if not np.isnan(y):
                fig.add_shape(x0=x0, x1=x1, y0=y, y1=y, line=self._connector_line)
    
    def _add_sumtotal(self, fig, X, tdf):
        # TODO: handle color
        x = X[self._x].max()
        if self._group is None:
            y = tdf[self._y].sum()
            self._add_total_bar_line(fig, x, y, 0, None)
        else:
            for groupno, (groupname, group) in enumerate(tdf.groupby(self._group, sort=False)):
                y = group["Y"].sum()
                self._add_total_bar_line(fig, x, y, groupno, groupname)
        
    def _add_total_bar_line(self, fig, x, y, groupno, groupname):
        categoryname = self._total_column_name


        if isinstance(self._colors, dict) and (groupname in self._colors):
            color = self._colors[groupname]
        else:
            color = self._colors
        
        if isinstance(color, dict) and (categoryname in color):
            color = color[categoryname]

        fig.add_bar(
            x=[x+1], y=[y], offsetgroup=groupno, name=categoryname, marker_color=color,
            legendgroup=groupname, legendgrouptitle_text=groupname,
            width=self._barwidth, offset=-(self._barwidth+self._gap/2)*self.__totalgroups/2 + 
                (self._barwidth+self._gap/2)*groupno,
        )

        x0 = x-(self._barwidth+self._gap/2)*self.__totalgroups/2 + (self._barwidth+self._gap/2)*groupno
        x1 = x+1-(self._barwidth+self._gap/2)*self.__totalgroups/2 + (self._barwidth+self._gap/2)*groupno + self._barwidth
        fig.add_shape(x0=x0, x1=x1, y0=y, y1=y, line=self._connector_line)
