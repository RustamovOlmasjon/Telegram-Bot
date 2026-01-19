import yt_dlp
try:
    f = yt_dlp.utils.match_filter_func("duration > 60")
    print("Success: match_filter_func is available")
except AttributeError:
    print("Error: match_filter_func is NOT available")
except Exception as e:
    print(f"Error: {e}")
