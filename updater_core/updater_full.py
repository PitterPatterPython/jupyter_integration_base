from ipywidgets import Button, HBox, VBox, Label, Layout, Output
from IPython.display import display
from IPython.core.magic import magics_class, line_cell_magic
import textwrap
import jupyter_integrations_utility as jiu
from addon_core import Addon
from updater_core.styles import InstallIntegrationButton

@magics_class
class Updater(Addon):
    
    def __init__(self, shell, debug=False, *args, **kwargs):
        super(Updater, self).__init__(shell, debug=False)
        self.debug = debug
        self.output = Output()
    
    def customHelp(self, curout):
        if "integrations_cfg" not in self.ipy.user_ns:
            jiu.display_error("Integrations config file isn't loaded into your environment. Try \
                restarting your kernel, or contact an admin.")
        else:
            repos = self.ipy.user_ns["integrations_cfg"]["repos"]
            
            loaded_integrations = list(self.ipy.user_ns["jupyter_loaded_integrations"].keys())
            loaded_integrations = [f"jupyter_{integration}" for integration in loaded_integrations] #<-- consider changing this wherever it's originally created
            loaded_integrations.sort()
            
            available_integrations = list(repos.keys())
            available_integrations = list(set(available_integrations).difference(loaded_integrations)) # Get rid of items that are already loaded
            available_integrations.sort()            

            ######################################################
            # Create the table for Loaded/Installed Integrations #
            ######################################################
            loaded_rows = []
            title_row = HBox([Label(value="Installed Integrations", style=dict(font_weight="bold", font_size="18px"))])
            header_row = HBox([Label(value="Integration", style=dict(font_weight="bold"), layout=Layout(display="flex", width="20%", justify_content="flex-start")),
                               Label("Repo URL", style=dict(font_weight="bold"), layout=Layout(display="flex", width="60%", justify_content="flex-start")),
                               Label("", layout=Layout(display="flex", width="10%"))]
                              )
            loaded_rows.append(title_row)
            loaded_rows.append(header_row)
            
            for integration in loaded_integrations:

                install_button = InstallIntegrationButton(value = integration,
                                                  description = "Re-install",
                                                  button_style = "info",
                                                  layout = Layout(
                                                      display = "flex",
                                                      width="10%",
                                                      justify_content = "center"
                                                      
                                                  ))
                install_button.on_click(self.on_click)
                
                loaded_rows.append(HBox([Label(integration.replace("jupyter_", "").capitalize(), layout=Layout(display="flex", width="20%", justify_content="flex-start")), 
                                         Label(repos[integration]["repo"], layout=Layout(display="flex", width="60%", justify_content="flex-start")), 
                                         install_button]
                                      )
                                 )
            ###############################################
            # Create the table for Available integrations #
            ###############################################
            available_rows = []
            title_row = HBox([Label(value="Available Integrations", style=dict(font_weight="bold", font_size="18px"))])
            header_row = HBox([Label(value="Integration", style=dict(font_weight="bold"), layout=Layout(display="flex", width="20%", justify_content="flex-start")),
                               Label("Repo URL", style=dict(font_weight="bold"), layout=Layout(display="flex", width="60%", justify_content="flex-start")),
                               Label("", layout=Layout(display="flex", width="10%"))]
                              )
            available_rows.append(title_row)
            available_rows.append(header_row)
            
            for integration in available_integrations:
                install_button = InstallIntegrationButton(value = integration,
                                                  description = "Install",
                                                  button_style = "info",
                                                  layout = Layout(
                                                      display = "flex",
                                                      width = "10%",
                                                      justify_content = "center"
                                                  ))
                
                install_button.on_click(self.on_click)
                
                available_rows.append(HBox([Label(integration.replace("jupyter_", "").capitalize(), layout=Layout(display="flex", width="20%", justify_content="flex-start")), 
                                       Label(repos[integration]["repo"], layout=Layout(display="flex", width="60%", justify_content="flex-start")), 
                                       install_button]
                                      )
                                 )
            
            
            full_table = VBox([VBox(loaded_rows, layout=Layout(display="flex", width="100%", flex_flow="column", align_items="stretch")),
                               VBox(available_rows, layout=Layout(display="flex", width="100%", flex_flow="column", align_items="stretch"))
                               ])
            
            display(full_table, self.output)
            
            output = "" # addon_base doesn't allow non-Markdown output, so I override it
            return output
    
    def on_click(self, b):
        with self.output:
            print(f"\r{' ' * 50}", end="") # Overwrite longer lines of text
            print(f"\r{b.value}", end="")
    
    # This is the magic name.
    @line_cell_magic
    def updater(self, line, cell=None):
        if self.debug:
           print("line: %s" % line)
           print("cell: %s" % cell)
        
        if cell is None:
            line_handled = self.handleLine(line)
        
            if not line_handled: # We based on this we can do custom things for integrations. 
        
                if line.lower().find("functions") == 0:
                    newline = line.replace("functions", "").strip()
        
                    if newline == "":
                        self.pyvis_help(None)
        
                    else:
                        self.pyvis_help(newline)
                else:
                    print("I am sorry, I don't know what you want to do with your line magic, try just %" + self.name_str + " for help options")
        
        else: # This is run is the cell is not none, thus it's a cell to process  - For us, that means a query
            print("No Cell Magic for %s" % self.name_str)