#link to tutorial https://www.youtube.com/watch?v=taZYIqC7VMM
from shiny import (
    App, ui, render, reactive, Session
    )
from shinywidgets import (
      output_widget, render_widget
    )


from htmltools import css
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import yfinance as yf
import asyncio
from datetime import date

#info of the page (title window size)
TITLE = "PyShiny Financial Stock Analyzer Demo"
symbol  = "AAPL"
period ="1y"
window_mavg_short =30
window_mavg_long =90

#using yahoo API to get date

stock_data = yf.download(symbol, start='2020-01-01', end='2023-07-01')
stock = yf.Ticker(symbol)  
stock_info = stock.info
stock_history = stock.history(period=period)

#fonction to create info cards
def my_card(title, value, width=4,bg_color="bg-dark", text_color="text-white"):
  card_ui = ui.div(
      ui.div(
        ui.div(
          ui.div(ui.h4(title), class_="card-title"),
          ui.div(value, class_="card-text"),
          class_="card-body flex-fill"
        ),
        class_=f"card{text_color}{bg_color}",
        style="flex-grow:1;margin:5px;"
      ),
      class_=f"col-md-{width} d-flex"
  )
  return card_ui


def make_ploty_chart(stock_history, window_mavg_short=30, window_mavg_long =90):
    
  stock_df = stock_history[['Close']] \
    .reset_index()
        
  stock_df['mavg_short'] = stock_df['Close'] \
    .rolling(window = window_mavg_short) \
    .mean()
        
  stock_df['mavg_long'] = stock_df['Close']\
    .rolling(window = window_mavg_long)\
    .mean()
        
  fig = px.line(
    data_frame=stock_df.set_index('Date'),
    color_discrete_map={
      "Close":"#212529",
      "mavg_short":"#ff8b07",
      "mavg_long":"#0dcaf0"
    },
    title=None
  )
    
  fig = fig.update_layout(
    plot_bgcolor = 'rgba(0,0,0,0)',
    paper_bgcolor = 'rgba(0,0,0,0)',
    legend_title_text=''
  )
    
  fig = fig.update_yaxes(
    title="Share Price",
    tickprefix="$",
    gridcolor='#2c3e50'
  )
      
  fig = fig.update_xaxes(
    title="",
    gridcolor='#2c3e50'
  )
  return fig
#style the page with css file
page_dependencies = ui.tags.head(
      ui.tags.link(rel="stylesheet", type="text/css", href="style.css")
)
#--------------------------USER INTERFACE--------------------------#
app_ui = ui.page_navbar(
  ui.nav(
    "",
    ui.layout_sidebar(
      sidebar=ui.panel_sidebar(
        ui.h2("SELECT A STOCK"),
        ui.input_selectize(
          "stock_symbol",
          "Stock Symbol",
          ['AAPL', 'GOOG', 'MSFT'],
          selected='MSFT',
          multiple=False
        ),ui.download_button("downloadData", "Download_financials_tsv"),

        width=3
      ),
      main = ui.panel_main(
        ui.h2(
          ui.output_text("txt")
        ),
        ui.div(
          output_widget("stock_chart_widget", width="auto", height="auto"),
          class_="card"
        ),
        ui.navset_pill_card(
          ui.nav(
            "Company Summary",
            ui.output_ui("stock_info_ui")
          ),
          ui.nav(
            "Financials",
            ui.output_table("income_statement_table")
          )
        ),
      ),
    ), 
  ),
  title = ui.tags.div(
    ui.img(src="Avanade.png", height="50px", style="margin:5px;"),
    ui.h4(" " + TITLE),
    style="display:flex;-webkit-filter: drop-shadow(2px 2px 2px #222);"
  ),
  bg="#ff8b07",
  inverse=True,
  header=page_dependencies    
)
    
#--------------------------SERVER--------------------------#

def server(input, output,session:Session):

  #reactivity by changing the symbol "MSFT"...
  @reactive.Calc
  def stock():
    return yf.Ticker(str(input.stock_symbol()))
        
  @output
  @render.text
  def txt():
    return f"{str(input.stock_symbol())}"
  

  @output 
  @render_widget
  def stock_chart_widget():
    fig=make_ploty_chart(stock_history, window_mavg_short, window_mavg_long)
    return go.FigureWidget(fig)
  
  
     
  #info cards : Company Information
  
  @output
  @render.ui
  def stock_info_ui():
      stock_info = stock().info
      app_ui = ui.row(
        ui.h5("Company Information"),
        my_card("Industry", stock_info['industry'], bg_color="bg-dark"),
        my_card("Fulltime Employees", "{:0,.0f}".format(stock_info
        ['fullTimeEmployees']), bg_color="bg-dark"),
        my_card("Website", ui.a(stock_info['website'],href=stock_info['website'],
        target_="blank"), bg_color="bg-dark"),

        ui.hr(),

        ui.h5("Financial Ratios"),
        my_card("Profit Margin", "{:0,.1%}".format(stock_info
        ['profitMargins']), bg_color="bg-primary"),
        my_card("Revenue Growth", "{:0,.1%}".format(stock_info
        ['revenueGrowth']), bg_color="bg-primary"),
        my_card("Current Ratio", "{:0,.2f}".format(stock_info
        ['currentRatio']), bg_color="bg-primary"),

        ui.hr(),


        ui.h5("Financial Operations"),
        my_card("Total Revenue", "{:0,.0f}".format(stock_info
        ['totalRevenue']), bg_color="bg-info"),
        my_card("EBITDA", "{:0,.0f}".format(stock_info
        ['ebitda']), bg_color="bg-info"),
        my_card("Operatinf Cash F", "{:0,.0f}".format(stock_info
        ['operatingCashflow']), bg_color="bg-info")
      )
      return app_ui

  #financial main chart
  @output 
  @render_widget
  def stock_chart_widget():
    stock_history = stock().history(period=period)
    fig=make_ploty_chart(stock_history, window_mavg_short, window_mavg_long)
    return go.FigureWidget(fig)
  
  #financials table
  @output
  @render.table
  def income_statement_table():
    stock_incomestmt = stock().financials
    return(
      stock_incomestmt \
        .reset_index()
    )
  #download section
  @session.download(filename=lambda: f"financials-{str(input.stock_symbol())}-{date.today().isoformat()}-{np.random.randint(100,999)}.csv")
  async def downloadData():
        await asyncio.sleep(0.25)
        stock_incomestmt = stock().financials
        yield stock_incomestmt.to_string(index=False)

#define the www folder (for favicon, css file...)
www_dir = Path(__file__).parent / "www"

#create a shiny object by calling the App funtion (link the ui and server)
app = App(app_ui, server, static_assets=www_dir)

