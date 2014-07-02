Autopsy
==============

![Autopsy Logo](https://github.com/davelab6/autopsy/raw/master/logo.png)

Autopsy is a [Glyphs](http://glyphsapp.com/) plugin for analyzing design consistency across multiple fonts.

![Screen shot of the Autopsy interface](https://github.com/davelab6/autopsy/raw/master/showing.png)

It visualizes a selection of letters side by side and puts it into a PDF for visual comparison. If visual comparison isn’t enough for you, it dissects what’s there and what’s not and puts that into simple graphs.

#### Single fonts

Compare the design of glyphs across different fonts or families. Something you can’t do in FontLab without generating each font an loading them into some document.

#### Multiple Master instances

Multiple Master fonts are not supported yet. 

Donate
---------

If you’re using this for something useful, and you see the amount of work Yanone put into it, please consider to thank him with a donation to his PayPal account, *post@yanone.de*.

<form action="https://www.paypal.com/cgi-bin/webscr" method="post"><input type="hidden" name="cmd" value="_donations"><input type="hidden" name="business" value="post@yanone.de"><input type="hidden" name="lc" value="US"><input type="hidden" name="item_name" value="Yanone's free fonts"><input type="hidden" name="currency_code" value="EUR"><input type="hidden" name="bn" value="PP-DonationsBF:btn_donateCC_LG.gif:NonHostedGuest"><input type="image" src="http://www.paypal.com/en_US/i/btn/btn_donateCC_LG.gif" border="0" name="submit" alt="PayPal - The safer, easier way to pay online!"><img alt="" border="0" src="http://www.paypal.com/en_US/i/scr/pixel.gif" width="1" height="1"></form>

Install
---------

Double click the file Autopsy.glyphsPlugin and follow the dialogs.

Licence
------------

Autopsy is libre software, licensed under the terms of the GNU GPLv3


Recent changes
---------------

- Ported as much functionality as possible to the plugin APIs. 
- Use a .nib for the interface. This removes the dependency to vanilla. 
- use CoreGraphics to write the pdf. This remove the dependency to reportlab.
