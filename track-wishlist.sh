#!/bin/bash

tmp=$(mktemp)
for wl in EZ5T4B4IF5UW; do
    /usr/local/bin/amazon-wishlist-price-tracker/track-wishlist.py $wl 2>/dev/null >$tmp
    test -s $tmp && mail -s "Amazon-Wishlist: $wl" my.user.name@gmail.com <$tmp
done
rm -f $tmp
