package com.bray.watcher;

import android.os.Build;
import android.service.quicksettings.Tile;
import android.service.quicksettings.TileService;

import androidx.annotation.RequiresApi;

/**
 * Quick settings tile toggling Bray's focus mode.
 */
@RequiresApi(api = Build.VERSION_CODES.N)
public class BrayTileService extends TileService {

    @Override
    public void onTileAdded() {
        Tile tile = getQsTile();
        if (tile != null) {
            tile.setLabel("Bray");
            tile.setContentDescription("Tap for focus mode");
            tile.setState(Tile.STATE_INACTIVE);
            tile.updateTile();
        }
    }

    @Override
    public void onClick() {
        Tile tile = getQsTile();
        if (tile == null) {
            return;
        }
        if (tile.getState() == Tile.STATE_INACTIVE) {
            startFocusMode();
            tile.setState(Tile.STATE_ACTIVE);
            tile.setLabel("FOCUS ON");
        } else {
            stopFocusMode();
            tile.setState(Tile.STATE_INACTIVE);
            tile.setLabel("Bray");
        }
        tile.updateTile();
    }

    private void startFocusMode() {
        FocusMode focusMode = new FocusMode(this);
        focusMode.enableFocus(90);
    }

    private void stopFocusMode() {
        FocusMode focusMode = new FocusMode(this);
        focusMode.disableFocus();
    }
}
