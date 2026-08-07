// HIRI Web: room/area grouping + fuzzy search (#12)
class DeviceSearch {
    constructor(devices) {
        this.devices = devices;
    }
    
    byRoom(room) {
        return this.devices.filter(d => d.room === room);
    }
    
    byArea(area) {
        return this.devices.filter(d => d.area === area);
    }
    
    fuzzySearch(query) {
        const q = query.toLowerCase();
        return this.devices.filter(d =>
            d.name.toLowerCase().includes(q) ||
            d.room.toLowerCase().includes(q) ||
            (d.tags || []).some(t => t.toLowerCase().includes(q))
        );
    }
    
    groupByRoom() {
        const groups = {};
        for (const d of this.devices) {
            const room = d.room || 'unassigned';
            if (!groups[room]) groups[room] = [];
            groups[room].push(d);
        }
        return groups;
    }
    
    suggestions(partial, limit = 5) {
        return this.fuzzySearch(partial).slice(0, limit).map(d => ({
            label: `${d.name} (${d.room})`,
            id: d.id
        }));
    }
}

if (typeof module !== 'undefined') module.exports = DeviceSearch;
