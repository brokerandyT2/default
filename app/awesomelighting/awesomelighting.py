import hassapi as hass
import datetime 
from numpy import number
from suncalc import  get_times
from time import sleep
 
 
class BedroomLights(hass.Hass):

    def initialize(self):

        #Must be an Array
        self.light = self.args.get("light", ["light.group_all"])
        #Must be an Array
        self.motion_sensor = self.args.get("motion_sensor")

        self.trigger_time_start = self.args.get("trigger_time_start", 0)
        #self.trigger_time_end = self.args.get("trigger_time",0)
        self.trigger_start_offset = self.args.get("trigger_start_offset",0)
        #self.trigger_end_offset = self.args.get('trigger_end_offset',0)
        self.sun_event_start = self.args.get("sun_event_start", "default")
        #self.sun_event_end = self.args.get("sn_event_end", "sunset_end")
        self.lat = self.args.get("lat", 0.0)
        self.long = self.args.get("long", 0.0)
        self.x_color = self.args.get("x_color",0.0)
        self.y_color = self.args.get("y_color",0.0)
        self.brightness = self.args.get("brightnss",128)
        self.time_to_off = self.args.get("time_to_off", 0)
        self.transistion = self.args.get("transistion", False)
        self.transisition_time_in_seconds = self.args.get("transisition_time_in_seconds", 0)
        self.state_holder = self.args.get("state_holder", "input_boolean")
        self.input_bools_to_turn_off = self.args.get("input_bools_to_turn_off", [])
        
        if(len(self.input_bools_to_turn_off)>0):
            for boo in self.input_bools_to_turn_off:
                hass.Hass.turn_off(self, boo)
        
        
        if(self.GetinputBooleanStatus(self.state_holder) == True):
            self.log("Script has already been run.  Please check the input boolean :" +self.state_holder)
            return        
        self.write_to_logs = self.args.get("write_to_logs", False)
        
        #defaults
        self.inputboolstate = "off"
        self.startingBrightness = 0
        self.currentXY = []
        
        #turn on light and get its current state
        
        hass.Hass.turn_on(self, self.light[0])        
        self.light_state = hass.Hass.get_state(self, self.light[0], attribute="all")
        #shut light back off
        hass.Hass.turn_off(self, self.light[0])
        if(self.write_to_logs):
            self.log("Light State for: "+ self.light[0])
            self.log(self.light_state)
            
        #get State of Tracking toggle in HA
        self.state_tracking_bool = self.GetinputBooleanStatus(self.state_holder)
        if(self.write_to_logs):
            self.log("Boolean State for: "+ self.state_holder)
            self.log(self.state_tracking_bool)        
        deltaX = 0
        deltaY = 0
        deltaBrightness = 0
        
        
        #lights that are off do not return attributes.  Since they are off, we assume things are zeros
        if(self.light_state["attributes"]["xy_color"] == None):
            self.current_x = 0
            self.current_y = 0
            #we know that current is gonna be 0 and that we need to count "up", so take the abs of the subtraction (forcing it to positive)
            deltaX = abs(self.current_x - self.x_color)
            deltaY = abs(self.current_y - self.y_color)
            if(self.write_to_logs):            
                self.log("initalize: Set Transistion deltax")
                self.log(deltaX)
                self.log("initalize: Set for Transistion deltay")                                                          
                self.log(deltaY)             
        else:    
            self.current_x = self.light_state["attributes"]["xy_color"][0]
            self.current_y = self.light_state["attributes"]["xy_color"][1]
            deltaX = self.current_x - self.x_color
            deltaY = self.current_y - self.y_color
            
        #lights that are off do not return attributes.  Since they are off, we assume things are zeros
        if(self.light_state["attributes"]["brightness"] == None):
            if(self.write_to_logs):
                    self.log("initalize: entity brightness none")
            self.current_brightness = 0
            #we know that current is gonna be 0 and that we need to count "up", so take the abs of the subtraction (forcing it to positive)
            deltaBrightness = abs(self.current_brightness - self.brightness)
            if(self.write_to_logs):
                    self.log("initalize: deltaBrightness Value: ")            
                    self.log(deltaBrightness)            
            
        else:
            if(self.write_to_logs):
                    self.log("initalize: entity brightness exists")            
            self.current_brightness = self.light_state["attributes"]["brightness"]
            deltaBrightness = self.current_brightness - self.brightness
                
        if(self.transisition_time_in_seconds !=0 and self.transistion == True):

            self.x_color_step_change = round(deltaX / self.transisition_time_in_seconds, 3)
            self.y_color_step_change = round(deltaY/self.transisition_time_in_seconds, 3)
            if(self.write_to_logs):
                self.log("initalize: Call for Transistion")
                self.log("initalize: Call for Transistion self.x_color_step_change")
                self.log(self.x_color_step_change)
                self.log("initalize: Call for Transistion self.y_color_step_change")                                                          
                self.log(self.y_color_step_change)
                self.log("initalize: Call for Transistion deltax")
                self.log(deltaX)
                self.log("initalize: Call for Transistion deltay")                                                          
                self.log(deltaY)                                   
        else:
            if(self.write_to_logs):
                self.log("initalize: call for no transistion")            
            self.x_color_step_change = self.x_color 
            self.y_color_step_change = self.y_color
                    
        if(self.brightness !=0 and self.transistion == True):
          
            self.brightness_step_change = round(deltaBrightness/self.transisition_time_in_seconds)
            if(self.write_to_logs):
                self.log("initalize: entity brightness with transistion")
                self.log("initalize: self.brightness_step_change")
                self.log(self.brightness_step_change)
        else:
            if(self.write_to_logs):
                self.log("initalize: entity brightness without transistion") 
            self.brightness_step_change = self.brightness
            
        #self.Validate(self)
        self.BuildDates()
        
        if(len(self.motion_sensor) ==1):        
            self.listen_state(self.motion_detected, self.motion_sensor)
        else:
            for entity in self.motion_sensor:
                #create a listener for each motion sensor that is passed in
                self.listen_state(self.motion_detected, entity)
                
    #def Validate(self):
    
    def BuildDates(self):
        currentDate = datetime.datetime.now()
        
        if(self.trigger_time_start != 0):
            if(self.write_to_logs):
                self.log("Start Time Configured: ")
                self.log(self.trigger_time_start)
            holderArray = self.trigger_time_start.split(":")
            self.trigger_date_time = datetime.datetime(year = currentDate.year, month=currentDate.month, day = currentDate.day, hour=int(holderArray[0]), minute=int(holderArray[1]), second=0 )      
        
        if(self.sun_event_start != "default" and self.trigger_time_start == 0):
            self.sun_time_start = get_times(datetime.datetime.now(), self.long, self.lat)[self.sun_event_start]
        
        if(self.trigger_start_offset != 0):
            self.sun_time_start = self.sun_time_start + datetime.timedelta(minutes=self.trigger_start_offset)
        
    def GetinputBooleanStatus(self, entity) -> bool:
        state = hass.Hass.get_state(self, entity)
        toReturn = False
        if(state == True):
            toReturn = True
            
        return toReturn
        
    def CompareDates(self, time) -> bool:
        return time > datetime.datetime.now()
            
    def ModifyLights(self):
        
        startTime = None
        
        if(self.sun_event_start != "default" or self.sun_event_start != "none"):
            startTime = self.sun_time_start + datetime.timedelta(minutes=self.trigger_start_offset)
        elif(self.sun_event_start == "default" or self.sun_event_start =="none"):
            startTime = self.trigger_date_time
        else:
            startTime = datetime.datetime.now()
        if(self.write_to_logs):
            self.log("Light Controller: start Time")
            self.log(startTime)    
        
        if(self.CompareDates(startTime)):
            x=0
            x_step = self.x_color_step_change
            y_step = self.y_color_step_change
            brightness_step= self.brightness_step_change
            if(self.write_to_logs):
                self.log("------------------- Current Values in Modify Lights -------------------")
                self.log("Light Controller: Current x color")
                self.log(self.current_x)
                self.log("Light Controller: Current y color")
                self.log(self.current_y)
                self.log("Light Controller: Current brightness")
                self.log(self.current_brightness)    
                self.log("Light Controller: x step")
                self.log(x_step)
                self.log("Light Controller: y step")
                self.log(y_step)
                self.log("Light Controller: brightness step")
                self.log(brightness_step)
                self.log("Light Controller: x Step Change")
                self.log(self.x_color_step_change)
                self.log("Light Controller: y Step Change")
                self.log(self.y_color_step_change)  
                self.log("------------------- End Current Values in Modify Lights -------------------")
            
            #build array for service call
            xy = [self.current_x, self.current_y]
            
            if(self.transisition_time_in_seconds ==0 or self.transistion == False):
                if(self.write_to_logs):                
                    self.log("True: self.transisition_time_in_seconds ==0 or self.transistion == False")
                    self.log("transisition_time_in_seconds")                
                    self.log(self.transisition_time_in_seconds)
                    self.log("transistion")
                    self.log(self.transistion)
                                        
                hass.Hass.turn_on(self, self.light[0], xy_color = xy, brightness = self.brightness)
            else:
                if(self.write_to_logs):                
                    self.log("False: self.transisition_time_in_seconds ==0 or self.transistion == False")
                    self.log("transisition_time_in_seconds")                
                    self.log(self.transisition_time_in_seconds)
                    self.log("transistion")
                    self.log(self.transistion)
                i =0
                x = xy[0]
                y = xy[1]
                bright = self.current_brightness
                #"turn on" light to begin modify (usecase: light is off).  Else, light will be the "same" as it's last on state
                hass.Hass.turn_on(self, self.light[0], xy_color= xy, brightness = self.current_brightness)
                    
                while(i < self.transisition_time_in_seconds):
                    #positive or negative . . . we will always add
                    x = x + x_step
                    y = y + y_step
                    xy = [x,y]
                    bright = bright + brightness_step
                    if(self.write_to_logs):                        
                        self.log("Loop for Adjusting Lights")
                        self.log("x color value ")
                        self.log(x) 
                        self.log("x step value ")
                        self.log(x_step)                         
                        self.log("y color value")
                        self.log(y)
                        self.log("y step value")
                        self.log(y_step)                        
                        self.log("brightness value")
                        self.log(bright)
                        self.log("brightness step value")
                        self.log(brightness_step)                                                                                           
                    hass.Hass.turn_on(self, self.light[0], xy_color = xy, brightness = bright)
                    sleep(1)
                    i += 1
                                      
                #Make Sure we "get there"    
                hass.Hass.turn_on(self, self.light[0], xy_color=[self.x_color, self.y_color], brightness=self.brightness)    
                hass.Hass.turn_on(self, self.state_holder)
                    
                if(self.time_to_off != 0):
                    sleep(self.time_to_off)
                    hass.Hass.turn_off(self, self.light[0])
                    hass.Hass.turn_off(self, self.state_tracking_bool)
        return
            
    def motion_detected(self, entity_id, attribute, old, new, kwargs):
        
        if(self.write_to_logs):
            self.log("input boolean state: ")
            self.log(self.state_tracking_bool)
            
        #save some computation . . . shut down the motion detection if the script has already been triggered
        if(self.state_tracking_bool == True):
            if(self.write_to_logs):
                self.log("Input Boolean was On.  Exiting motion detection event.  Tracking Entity: "+self.state_holder)
            return
        
        #is there more than one light to iterate through?
        lengthOfLights = len(self.light)
        
        #self.sun_event == none should be used to represent a "default" configuration     
        if(self.sun_event_start == "none" or self.sun_event_start == "default"):
            if(self.transistion == False):
                xy = [self.x_color, self.y_color]
                for light in self.light:
                    hass.Hass.turn_on(self, light, brightness = self.brightness, xy_color = xy)
            else:
                self.ModifyLights()
        else:
            
            if(self.sun_time_start != 0):
                if(self.CompareDates(self.sun_time_start)):
                    if(self.transistion == False):
                        for light in self.light:
                            hass.Hass.turn_on(self, light, brightness = self.brightness, xy_color = xy) 
                    else:
                        self.ModifyLights()
        return                        
        
