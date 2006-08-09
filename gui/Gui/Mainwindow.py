#!/usr/bin/python

#---------------------------------------------------------------------------

""" Import externals """
import wx
import os.path
import sys
import wx.lib.mixins.listctrl as listmix

#---------------------------------------------------------------------------

""" Import scyther-gui components """
import Preference
import Attackwindow
import Scytherthread
import Icon
import Scyther.Claim as Claim

#---------------------------------------------------------------------------

""" Some constants """
ID_VERIFY = 100
ID_AUTOVERIFY = 101
ID_STATESPACE = 102
ID_CHECK = 103

#---------------------------------------------------------------------------

class MainWindow(wx.Frame):

    def __init__(self, opts, args):
        super(MainWindow, self).__init__(None, size=(600,800))

        self.opts = opts
        self.args = args

        self.dirname = os.path.abspath('.')

        self.filename = 'noname.spdl'
        self.load = False

        # test
        if opts.test:
            self.filename = 'scythergui-default.spdl'
            self.load = True

        # if there is an argument (file), we load it
        if len(args) > 0:
            filename = args[0]
            if filename != '' and os.path.isfile(filename):
                self.filename = filename
                self.load = True

        Icon.ScytherIcon(self)

        self.CreateInteriorWindowComponents()
        self.CreateExteriorWindowComponents()

        aTable = wx.AcceleratorTable([
                                      #(wx.ACCEL_ALT,  ord('X'), exitID),
                                      (wx.ACCEL_CTRL, ord('W'), wx.ID_EXIT),
                                      (wx.ACCEL_NORMAL, wx.WXK_F1,
                                          ID_VERIFY),
                                      (wx.ACCEL_NORMAL, wx.WXK_F2,
                                          ID_STATESPACE),
                                      (wx.ACCEL_NORMAL, wx.WXK_F5, 
                                          ID_CHECK),
                                      (wx.ACCEL_NORMAL, wx.WXK_F6,
                                          ID_AUTOVERIFY),
                                      ])
        self.SetAcceleratorTable(aTable)

        self.claimlist = []
        self.pnglist = []

        #self.SetTitle(self.title) 

        self.firstCommand()

    def CreateInteriorWindowComponents(self):
        ''' Create "interior" window components. In this case it is just a
            simple multiline text control. '''

        ## Make zoom buttons
        #sizer = wx.BoxSizer(wx.VERTICAL)
        #buttons = wx.BoxSizer(wx.HORIZONTAL)
        #bt = wx.Button(self,ID_VERIFY)
        #buttons.Add(bt,0)
        #self.Bind(wx.EVT_BUTTON, self.OnVerify, bt)
        #bt = wx.Button(self,ID_STATESPACE)
        #buttons.Add(bt,0)
        #self.Bind(wx.EVT_BUTTON, self.OnStatespace, bt)
        #sizer.Add(buttons, 0, wx.ALIGN_LEFT)

        # Top: input
        self.top = wx.Notebook(self,-1)
        self.control = wx.TextCtrl(self.top, style=wx.TE_MULTILINE)
        if self.load:
            textfile = open(os.path.join(self.dirname, self.filename), 'r')
            self.control.SetValue(textfile.read())
            os.chdir(self.dirname)
            textfile.close()
        self.top.AddPage(self.control,"Protocol description")
        self.settings = SettingsWindow(self.top,self)
        self.top.AddPage(self.settings,"Verification parameters")

        #sizer.Add(self.top,1,wx.EXPAND,1)
        #self.SetSizer(sizer)

    def CreateExteriorWindowComponents(self):
        ''' Create "exterior" window components, such as menu and status
            bar. '''
        self.CreateMenus()
        self.SetTitle()

    def CreateMenu(self, bar, name, list):

        fileMenu = wx.Menu()
        for id, label, helpText, handler in list:
            if id == None:
                fileMenu.AppendSeparator()
            else:
                item = fileMenu.Append(id, label, helpText)
                self.Bind(wx.EVT_MENU, handler, item)
        bar.Append(fileMenu, name) # Add the fileMenu to the MenuBar


    def CreateMenus(self):
        menuBar = wx.MenuBar()
        self.CreateMenu(menuBar, '&File', [
             (wx.ID_OPEN, '&Open', 'Open a new file', self.OnOpen),
             (wx.ID_SAVE, '&Save', 'Save the current file', self.OnSave),
             (wx.ID_SAVEAS, 'Save &As', 'Save the file under a different name',
                self.OnSaveAs),
             (None, None, None, None),
             (wx.ID_EXIT, 'E&xit\tCTRL-W', 'Terminate the program',
                 self.OnExit)])
        self.CreateMenu(menuBar, '&Verify',
             [(ID_VERIFY, '&Verify protocol\tF1','Verify the protocol in the buffer using Scyther',
                 self.OnVerify) ,
             (ID_STATESPACE, 'Generate &statespace\tF2','TODO' ,
                 self.OnStatespace) ,
             (None, None, None, None),
             (ID_CHECK, '&Check protocol\tF5','TODO',
                 self.OnCheck) ,
             (ID_AUTOVERIFY, 'Verify &automatic claims\tF6','TODO',
                 self.OnAutoVerify) 
             ])
        self.CreateMenu(menuBar, '&Help',
            [(wx.ID_ABOUT, '&About', 'Information about this program',
                self.OnAbout) ])
        self.SetMenuBar(menuBar)  # Add the menuBar to the Frame


    def SetTitle(self):
        # MainWindow.SetTitle overrides wx.Frame.SetTitle, so we have to
        # call it using super:
        super(MainWindow, self).SetTitle('Scyther: %s'%self.filename)

    # Helper methods:

    def defaultFileDialogOptions(self):
        ''' Return a dictionary with file dialog options that can be
            used in both the save file dialog as well as in the open
            file dialog. '''
        return dict(message='Choose a file', defaultDir=self.dirname,
                    wildcard='*.spdl')

    def askUserForFilename(self, **dialogOptions):
        dialog = wx.FileDialog(self, **dialogOptions)
        if dialog.ShowModal() == wx.ID_OK:
            userProvidedFilename = True
            self.filename = dialog.GetFilename()
            self.dirname = dialog.GetDirectory()
            self.SetTitle() # Update the window title with the new filename
        else:
            userProvidedFilename = False
        dialog.Destroy()
        return userProvidedFilename

    # Event handlers:

    def OnAbout(self, event):
        msg = "Scyther GUI\n\nScyther and Scyther GUI\ndeveloped by Cas Cremers"
        dialog = wx.MessageDialog(self,msg, 'About scyther-gui', wx.OK)
        dialog.ShowModal()
        dialog.Destroy()

    def OnExit(self, event):
        self.Close()  # Close the main window.

    def OnSave(self, event):
        textfile = open(os.path.join(self.dirname, self.filename), 'w')
        textfile.write(self.control.GetValue())
        textfile.close()

    def OnOpen(self, event):
        if self.askUserForFilename(style=wx.OPEN,
                                   **self.defaultFileDialogOptions()):
            textfile = open(os.path.join(self.dirname, self.filename), 'r')
            self.control.SetValue(textfile.read())
            textfile.close()

    def OnSaveAs(self, event):
        if self.askUserForFilename(defaultFile=self.filename, style=wx.SAVE,
                                   **self.defaultFileDialogOptions()):
            self.OnSave(event)
            os.chdir(self.dirname)

    def RunScyther(self, mode):
        s = Scytherthread.ScytherRun(self,mode)

    def OnVerify(self, event):
        self.RunScyther("verify")

    def OnAutoVerify(self, event):
        self.RunScyther("autoverify")

    def OnStatespace(self, event):
        self.RunScyther("statespace")

    def OnCheck(self, event):
        self.RunScyther("check")

    def firstCommand(self):
        if self.opts.command:
            # Trigger a command automatically
            self.Show(True)
            self.RunScyther(self.opts.command)
                

#---------------------------------------------------------------------------

class SettingsWindow(wx.Panel):

    def __init__(self,parent,daddy):
        wx.Panel.__init__(self,parent,-1)

        self.win = daddy

        # Bound on the number of runs
        self.maxruns = int(Preference.get('maxruns','5'))
        r1 = wx.StaticText(self,-1,"Maximum number of runs (0 disables bound)")
        l1 = wx.SpinCtrl(self, -1, "",style=wx.RIGHT)
        l1.SetRange(0,100)
        l1.SetValue(self.maxruns)
        self.Bind(wx.EVT_SPINCTRL,self.EvtRuns,l1)

        # Matchin options
        self.match = int(Preference.get('match','0'))
        claimoptions = ['typed matching','find basic type flaws','find all type flaws']
        r2 = wx.StaticText(self,-1,"Matching type")
        l2 = self.ch = wx.Choice(self,-1,choices=claimoptions)
        l2.SetSelection(self.match)
        self.Bind(wx.EVT_CHOICE,self.EvtMatch,l2)

        ### MISC expert stuff

        # Bound on the number of classes/attacks
        self.maxattacks = int(Preference.get('maxattacks','100'))
        stname = Claim.stateDescription(True,2,False)
        atname = Claim.stateDescription(False,2,False)
        txt = "%s/%s" % (stname,atname)
        r9 = wx.StaticText(self,-1,"Maximum number of %s for all claims combined (0 disables maximum)" % txt)
        l9 = wx.SpinCtrl(self, -1, "",style=wx.RIGHT)
        l9.SetRange(0,100)
        l9.SetValue(self.maxattacks)
        self.Bind(wx.EVT_SPINCTRL,self.EvtMaxAttacks,l9)

        self.misc = Preference.get('scytheroptions','')
        r10 = wx.StaticText(self,-1,"Additional parameters for the Scyther tool")
        l10 = wx.TextCtrl(self,-1,self.misc,size=(150,-1))
        self.Bind(wx.EVT_TEXT,self.EvtMisc,l10)

        # Combine
        space = 10
        sizer = wx.FlexGridSizer(cols=3, hgap=space,vgap=space)
        sizer.AddMany([ l1,r1, (0,0),
                        l2,r2, (0,0),
                        l9,r9, (0,0),
                        l10,r10, (0,0),
                        ])
        self.SetSizer(sizer)
        self.SetAutoLayout(True)

    def EvtMatch(self,evt):
        self.match = evt.GetInt()

    def EvtRuns(self,evt):
        self.maxruns = evt.GetInt()

    def EvtMaxAttacks(self,evt):
        self.maxattacks = evt.GetInt()

    def EvtMisc(self,evt):
        self.misc = evt.GetString()

    def ScytherArguments(self,mode):
        """ Note: constructed strings should have a space at the end to
            correctly separate the options.
        """

        tstr = ""

        # Number of runs
        tstr += "--max-runs=%s " % (str(self.maxruns))
        # Matching type
        tstr += "--match=%s " % (str(self.match))
        # Max attacks/classes
        if self.maxattacks != 0:
            tstr += "--max-attacks=%s " % (str(self.maxattacks))

        # Verification type
        if mode == "check":
            tstr += "--check "
        elif mode == "autoverify":
            tstr += "--auto-claims "
        elif mode == "statespace":
            tstr += "--state-space "

        # Anything else?
        if self.misc != "":
            tstr += " " + self.misc + " "

        return tstr

#---------------------------------------------------------------------------


    

