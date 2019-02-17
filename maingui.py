# GUI Stuff
from tkinter import *
from tkinter import ttk
import os, sys
import tempfile
import time

# yuu Stuff
from yuu.downloader import *
from yuu.parser import webparse, webparse_m3u8, parsem3u8
from yuu.common import __version__

canvas = (400, 300)

root = Tk()
root.title("yuu - AbemaTV Downloader (WIP)")
root.minsize(canvas[0], canvas[1])
root.maxsize(canvas[0], canvas[1])
root.iconbitmap(r'icon.ico')

def validate_data(*args):
    x = inputlink.get()
    if x:
        if 'abema.tv' not in x:
            dlbutton.config(state='disabled')
        else:
            dlbutton.config(state="normal")
    else:
        dlbutton.config(state='disabled')

def main(*args):
    input_ = inputlink.get()
    res_ = resvar.get()
    verbose = False # Global set

    try:
        proxy_ = inputproxy.get()
    except:
        proxy_ = None
    
    try:
        output = outputFile.get()
    except:
        output = None

    outputText.set('Testing Proxy...')

    sesi = requests.Session()
    if proxy_:
        try:
            sesi.get('http://httpbin.org/get') # Some test website to check if proxy works or not
            sesi.proxies = {'http': proxy_, 'https': proxy_}
        except:
            sesi = requests.Session()
            sesi.proxies = {'http': proxy_}
            try:
                sesi.get('http://httpbin.org/get') # This too but in https mode
            except:
                sesi = requests.Session()
                sesi.proxies = {'https': proxy_} # Final test if it's failed then it will return error
                try:
                    sesi.get('http://httpbin.org/get')
                except:
                    outputText.set('[ERROR] Cannot connect to proxy (Request timeout)')
                    sys.exit(1)

    outputText.set('Fetching user token...')

    authtoken = getAuthToken(sesi, verbose)
    sesi.headers.update({'Authorization': authtoken[0]})

    if input_[-5:] != '.m3u8':
        outputText.set('Parsing website...')
        outputtitle, m3u8link = webparse(input_, res_, sesi, verbose)
        outputText.set('Parsing m3u8...')
        files, iv, ticket = parsem3u8(m3u8link, sesi, verbose)
        if output:
            if output[-3:] == '.ts':
                output = output
            else:
                output = output + '.ts'
        else:
            output = '{x} (AbemaTV {r}).ts'.format(x=outputtitle, r=res_)
    elif input_[-5:] == '.m3u8':
        outputText.set('Parsing m3u8...')
        outputtitle, res = webparse_m3u8(input_, sesi, verbose)
        files, iv, ticket = parsem3u8(input_, sesi, verbose)
        if output:
            if output[-3:] == '.ts':
                output = output
            else:
                output = output + '.ts'
        else:
            output = '{x} (AbemaTV {r}).ts'.format(x=outputtitle, r=res)

    # Don't use forbidden/illegal character (replace it with underscore)
    illegalchar = ['/', '<', '>', ':', '"', '\\', '|', '?', '*'] # https://docs.microsoft.com/en-us/windows/desktop/FileIO/naming-a-file
    for char in illegalchar:
       output = output.replace(char, '_')

    outputText.set('Fetching video key...')
    getkey = fetchVideoKey(ticket, authtoken, sesi, args.verbose)

    outputText.set('Downloading...')
    tempfolder = tempfile.mkdtemp()

    prog = ttk.Progressbar(root, length=canvas[0] * 2/3, mode='determinate', orient=HORIZONTAL)
    prog.grid(column=2, row=8, padx=(2, 2), pady=(5, 5), sticky=(W, S))
    prog["value"] = 0
    prog["maximum"] = len(files)
    dllist = []
    for f in files:
        outpath = simple_getVideo(f, getkey, iv, tempfolder, sesi)
        dllist.append(outpath)
        prog["value"] += 1
    prog.grid_forget()
    outputText.set('Merging...')
    mergeVideo(dllist, output)
    outputText.set('Done.')
    shutil.rmtree(tempfolder)

inputlink = StringVar()
resvar = StringVar()
inputproxy = StringVar()
outputText = StringVar()
outputFile = StringVar()
##progresstext = StringVar()

resopts = ('180p', '240p', '360p', '480p', '720p', '1080p')

ttk.Label(root, text="Input Link: ").grid(column=1, row=2, padx=(10, 2), pady=(10, 5))
ttk.Label(root, text="Resolution: ").grid(column=1, row=3, padx=(10, 2), pady=(5, 5))
ttk.Label(root, text="Proxy: ").grid(column=1, row=4, padx=(10, 2), pady=(5, 5))
ttk.Label(root, text="Output: ").grid(column=1, row=5, padx=(10, 2), pady=(5, 5))
##ttk.Label(root, textvariable=progresstext).grid(column=1, row=7, padx=(10, 2), pady=(5, 5))

EntryLink = ttk.Entry(root, width=50, textvariable=inputlink)   
EntryLink.grid(column=2, row=2, padx=(2, 10), pady=(10, 5), sticky=(W,E))
res = ttk.OptionMenu(root, resvar, *resopts)
res.grid(column=2, row=3, padx=(2, 2), pady=(5, 5), sticky=(W))
Proxy = ttk.Entry(root, width=50, textvariable=inputproxy)
Proxy.grid(column=2, row=4, padx=(2, 10), pady=(5, 5), sticky=(W,E))
OutputF = ttk.Entry(root, width=50, textvariable=outputFile)
OutputF.grid(column=2, row=5, padx=(2, 10), pady=(5, 5), sticky=(W,E))

outputStuff = ttk.Label(root, textvariable=outputText)
outputStuff.grid(column=2, row=7, padx=(2, 2), pady=(5, 5), sticky=(W,E))

dlbutton = ttk.Button(root, text='Download', command=main, width=50, state='disabled')
dlbutton.grid(column=2, row=6, padx=(2, 2), pady=(5, 5), sticky=(W, S))

inputlink.trace("w", validate_data)
resvar.trace("w", validate_data)

root.mainloop()