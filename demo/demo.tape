# Render with: vhs demo/demo.tape   (https://github.com/charmbracelet/vhs)
Output demo/demo.gif

Set Shell "bash"
Set FontSize 20
Set Width 1240
Set Height 680
Set Padding 22
Set Theme "Catppuccin Mocha"
Set WindowBar Colorful
Set TypingSpeed 50ms

Hide
Type `export PATH="$PWD/.venv/bin:$PATH" && clear` Enter
Sleep 1s
Show

Type "# clean a customer's messy exports and score the result against ground truth"
Enter
Sleep 900ms
Type "make sample-report"
Enter
Sleep 7s
