from ipywidgets import HBox, VBox, Label, Layout, Output
from IPython.display import display
from IPython.core.magic import magics_class, line_cell_magic
import jupyter_integrations_utility as jiu
from addon_core import Addon
from updater_core.updater_utils.styles import ButtonMaker
from updater_core.updater_utils.helpers import uninstall_integration, install_integration, cleanup_install, create_load_script

@magics_class
class Updater(Addon):
    
    def __init__(self, shell, debug=False, *args, **kwargs):
        super(Updater, self).__init__(shell, debug=False)
        self.debug = debug
        self.output = Output()
        self.repos = {}
        self.repos_to_ignore = ["jupyter_integration_base", "qgrid", "jupyter_dummy"]
    
    def customHelp(self, curout):
        if "integrations_cfg" not in self.ipy.user_ns:
            jiu.display_error("Integrations config file isn't loaded into your environment. Try \
                restarting your kernel, or contact an admin.")
        else:            
            self.repos = self.ipy.user_ns["integrations_cfg"]["repos"]
            
            loaded_integrations = list(self.ipy.user_ns["jupyter_loaded_integrations"].keys())
            loaded_integrations = [f"jupyter_{integration}" for integration in loaded_integrations]
            loaded_integrations.sort()
            
            
            # These are integrations that aren't loaded in the user's environment,
            # but are in the user's "integrations_cfg" list of repos.
            available_integrations = list(self.repos.keys())
            available_integrations = [i for i in available_integrations if i not in self.repos_to_ignore]
            available_integrations = list(set(available_integrations).difference(loaded_integrations)) # Get rid of items that are already loaded
            available_integrations.sort()            

            ######################################################
            # Create the table for Loaded Integrations #
            ######################################################
            loaded_rows = []
            title_row = HBox([Label(value="Installed Integrations", style=dict(font_weight="bold", font_size="18px"))])
            subtitle_row = HBox([
                Label(value="These integrations are already installed and loaded in your environment, and can be updated", 
                      style=dict(font_size="14px"), 
                      layout=Layout(display="flex", width="100%"))
                ])
            header_row = HBox([Label(value="Integration", style=dict(font_weight="bold"), layout=Layout(display="flex", width="20%", justify_content="flex-start")),
                               Label("Repo URL", style=dict(font_weight="bold"), layout=Layout(display="flex", width="60%", justify_content="flex-start")),
                               Label("", layout=Layout(display="flex", width="10%"))]
                              )
            loaded_rows.append(title_row)
            loaded_rows.append(subtitle_row)
            loaded_rows.append(header_row)
            
            for integration in loaded_integrations:

                install_button = ButtonMaker(value = integration,
                                             description = "Update",
                                             button_style = "info",
                                             origin = "loaded",
                                             layout = Layout(
                                                 display = "flex",
                                                 width="10%",
                                                 justify_content = "center"
                                                 ))
                install_button.on_click(self.on_click)
                
                loaded_rows.append(HBox([Label(integration.replace("jupyter_", "").capitalize(), layout=Layout(display="flex", width="20%", justify_content="flex-start")), 
                                         Label(self.repos[integration]["repo"], layout=Layout(display="flex", width="60%", justify_content="flex-start")), 
                                         install_button]
                                      )
                                 )
                
            ###############################################
            # Create the table for Available integrations #
            ###############################################
            available_rows = []
            title_row = HBox([Label(value="Available Integrations", style=dict(font_weight="bold", font_size="18px"))])
            subtitle_row = HBox([
                Label(value="These integrations can be loaded into your current environment (they won't be installed).", 
                      style=dict(font_size="14px"), 
                      layout=Layout(display="flex", width="100%", flex_flow="row wrap"))
                ])
            header_row = HBox([Label(value="Integration", style=dict(font_weight="bold"), layout=Layout(display="flex", width="20%", justify_content="flex-start")),
                               Label("Repo URL", style=dict(font_weight="bold"), layout=Layout(display="flex", width="60%", justify_content="flex-start")),
                               Label("", layout=Layout(display="flex", width="10%"))]
                              )
            available_rows.append(title_row)
            available_rows.append(subtitle_row)
            available_rows.append(header_row)
            
            for integration in available_integrations:
                install_button = ButtonMaker(value = integration,
                                             description = "Load",
                                             button_style = "info",
                                             origin = "available",
                                             layout = Layout(
                                                 display = "flex",
                                                 width = "10%",
                                                 justify_content = "center"
                                                 ))
                
                install_button.on_click(self.on_click)
                
                available_rows.append(HBox([Label(integration.replace("jupyter_", "").capitalize(), layout=Layout(display="flex", width="20%", justify_content="flex-start")), 
                                       Label(self.repos[integration]["repo"], layout=Layout(display="flex", width="60%", justify_content="flex-start")), 
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
        """An widgets event that's attached to each button, and called when clicked. Every
            button has an on_click attached to it.
            
            General order of operations below:
            1. Uninstall the integration depending on the button the user clicked,
                accessed by the "b.value" property.
            2. If the uninstallation was successful, attempt to install the integration
            3. Create a "load" script and display it to the user, which they can use
                to reload a currently installed integration, or add as a startup script
            4. Cleanup the installation regardless of what happens below. This includes
                - remove the .zip file
                - remove the unzipped (folder) file

        Args:
            b (Button): The button object that generated this on_click event
        """
        self.output.clear_output()
        
        try:
            with self.output:
                # First attempt to uninstall
                jiu.display_info(f"Force-uninstalling `{b.value}...")
                uninstall_code = uninstall_integration(b.value)                
                
                # Attempt to install the integration if the uninstall was successful
                if uninstall_code == 0:
                    jiu.display_info(f"Attempting to install `{b.value}`...")
                    repo_url = self.repos[b.value]["repo"]
                    proxies = self.ipy.user_ns["integrations_cfg"]["proxies"]
                    install_code = install_integration(b.value, repo_url, proxies)
                    
                    if install_code == 0:
                        self.output.clear_output()
                        jiu.display_success(f"Successfully installed `{b.value}`!")
                        
                        load_script = create_load_script(b.value.replace("jupyter_", ""))

                        if b.origin == "available":
                            jiu.display_warning(f"{b.value} is installed to your environment now, but you need to re-load your kernel and then run the code block below.")
                            jiu.displayMD(f"\n```\n{load_script}```")
                            
                        elif b.origin == "loaded":
                            jiu.display_warning(f"{b.value} has been re-installed, but you need to copy and run the code block below to re-load")
                            jiu.displayMD(f"\n```\n{load_script}```")
                            
                        else:
                            jiu.display_error("You clicked on a button that has no `origin` property set and that's bad.")
                            
                    else:
                        self.output.clear_output()
                        jiu.display_error(f"Error running install of {b.value}. Error code: `{install_code}`")
                    
                    # Cleanup the install regardless of the outcome
                    if self.debug:
                        jiu.display_info(f"Cleaning up after install of `{b.value}`...")
                    
                    cleanup_install(b.value)
                    
                    if self.debug:
                        jiu.display_info(f"Finished cleanup...")                    
                
                else:
                    jiu.display_error(f"Uninstall of {b.value} failed. This should never happen: contact an admin.")
            
        except Exception as ex:
            cleanup_install(b.value)
            jiu.display_error(ex)
    
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