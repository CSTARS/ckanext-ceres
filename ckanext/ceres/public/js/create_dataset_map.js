// Dataset map module
this.ckan.module('create-dataset-map', function (jQuery, _) {

  return {
    options: {
      i18n: {
      },
      styles: {
        point:{
          iconUrl: '/img/marker.png',
          iconSize: [14, 25],
          iconAnchor: [7, 25]
        },
        default_:{
          color: '#B52',
          weight: 2,
          opacity: 1,
          fillColor: '#FCF6CF',
          fillOpacity: 0.4
        }
      },
      style: {
          color: '#F06F64',
          weight: 2,
          opacity: 1,
          fillColor: '#F06F64',
          fillOpacity: 0.1
        },
      default_extent: [[90, 180], [-90, -180]]
    },
    extentLayer : null,

    initialize: function () {

      this.extent = this.el.data('extent');

      // hack to make leaflet use a particular location to look for images
      L.Icon.Default.imagePath = this.options.site_url + 'js/vendor/leaflet/images';

      jQuery.proxyAll(this, /_on/);
      this.el.ready(this._onReady);

    },

    _onReady: function(){
      var module = this;
      var map, backgroundLayer, extentLayer, ckanIcon;

      map = ckan.commonLeafletMap('dataset-map-container', {attributionControl: false});

      var ckanIcon = L.Icon.extend({options: this.options.styles.point});

      if (this.extent) {
          this.extentLayer = L.geoJson(this.extent, {
              style: this.options.styles.default_,
              pointToLayer: function (feature, latLng) {
                return new L.Marker(latLng, {icon: new ckanIcon})
              }});
          this.extentLayer.addTo(map);
      
          if (this.extent.type == 'Point'){
              map.setView(L.latLng(this.extent.coordinates[1], this.extent.coordinates[0]), 9);
          } else {
              map.fitBounds(this.extentLayer.getBounds());
          }
      } else {
          map.fitBounds(module.options.default_extent);
      }
      
      map.addControl(new L.Control.Draw({
          position: 'topright',
          polyline: false, polygon: false,
          circle: false, marker: false,
          rectangle: {
            shapeOptions: module.options.style,
            title: 'Draw rectangle'
          }
        }));
       
      map.on('draw:rectangle-created', function (e) {
          if (module.extentLayer) {
            map.removeLayer(module.extentLayer);
          }
          module.extentLayer = e.rect;
          
          // create geojson for box
          var line = module.extentLayer.getLatLngs();
          for( var i = 0; i < line.length; i++ ) {
              line[i] = [line[i].lng,line[i].lat]
          }
          var geojson = {
              "type":"Polygon",
              "coordinates":[line]
          }
          
          $('#'+module.el.attr('extra-id')).val(JSON.stringify(geojson));
          
          module.extentLayer = L.geoJson(geojson, {
              style: module.options.styles.default_,
              pointToLayer: function (feature, latLng) {
                return new L.Marker(latLng, {icon: new ckanIcon})
          }});
          
          map.addLayer(module.extentLayer);
        });
      
      

      
    }
  }
});