# sub_sync
Takes an srt subtitle file that is not synchronized to the specific release and synchronizes it automatically against a properly synchronized file. helpful when a subtitle file for a language is unavailable for the specific video release.
<br/><br/>
Usage:<br/>
python sync.py \<synchronized srt file path\> \<un-synchronized srt file path\> \<output path\><br/>
<br/>
For example:<br/>
  synchronized srt file path -    path to srt file in english that is synchronized with the movie file<br/>
  un-synchronized srt file path - path to srt file in russian that is not synchronized with the movie file (synchronized with a different release of the same movie)<br/>
  output path - path to the scripts output<br/>  
