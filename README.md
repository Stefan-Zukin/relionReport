# relionReport
RelionReport is a tool which generates a report and animation from a given relion 3DClass, Refine3D or InitialModel job. 
RelionReport aims to give more meaningful output from relion jobs to aid in making processing decisions and presenting processing data.

![GitHub Logo](/images/distribution.png)

## Installation
To run relionReport, you need a python environment with glob2, pandas and matplotlib installed. These libraries can be installed with pip or conda.

`pip install glob2 pandas matplotlib`

`conda create --name relionReport glob2 pandas matplotlib`

If you wish to create movies using relionReport, you need ChimeraX and ffmpeg installed as well. You must also specify where your ChimeraX executable file is located. To do this, open relionReport.py in a text editor, and modify the line

`CHIMERA_PATH = "/Applications/ChimeraX-1.1.1.app/Contents/MacOS/ChimeraX"` 

to specify the path to your ChimeraX executible. On linux, this is usually `/programs/x86_64-linux/chimera/1.13.1/bin/chimera`. On mac it is usually `/Applications/Chimera.app/Contents/MacOS/chimera`.

## Use
To generate a report, execute relionReport.py and pass your job folder in as an argument.

`python3 relionReport.py Class3D/job022`

This will create a report titled job022.pdf in the current working directory.

To also generate a movie of the job in ChimeraX, add the `-m` flag to your command.

`python3 relionReport.py -m Class3D/job022`

This will create a folder titled job022Images in the current working directory, which contains individual frames and the final rendered movie.

## Parameters

#### -i

-i opens the graphs in interactive mode, so you can modify them and save particular views

`python3 relionReport.py -i Class3D/job022`

#### -style [style]
-style allows you to specify a matplotlib style to be used when creating the report. The default is seaborn-paper.

`python3 relionReport.py -style ggplot Class3D/job022`

#### -v [ChimeraX commands]

-v allows you to specify ChimeraX commands to be executed before saving an image. This gives flexible control over visual style in ChimeraX.
The command should be enclosed in quotations and separate commands should be separated by semicolons.

`python3 relionReport.py -v "lighting flat; set silhouetteWidth 2" Class3D/job022`

#### -s [ChimeraX commands]

-s allows you to specify the parameters for ChimeraX image saving. This gives control over the output resolution, transparency and supersample levels.
The command should be enclosed in quotations.

`python3 relionReport.py -s "supersample 8 width 2048 height 2048 transparentBackground true" Class3D/job022`

## Other Notes

By default, ChimeraX sets the map levels at sdlevel = 6. This might be too high or too low a level depending on your particular project. To change the level, open relionReport.py in a text editor, and modify the line `LEVEL = 6` to your desired sdlevel.
`
