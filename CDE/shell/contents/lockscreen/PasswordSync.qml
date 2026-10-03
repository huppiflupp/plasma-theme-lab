pragma Singleton
import QtQuick

// One password for the greeters of all screens, as kscreenlocker's own
// theme keeps it.
QtObject {
    property string password
}
