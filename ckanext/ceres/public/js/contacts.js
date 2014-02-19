/****
 * Create the contact widgets for the input form
 ****/

ckan.module('ceres-form-contact', function (jQuery, _) {
    var template = [
       '<div>',
           '',
           '<div class="control-group">',
               '<label class="control-label" for="cc-name-{{prefix}}">Contact Name</label>',
               '<div class="controls">',
                 '<input id="cc-name-{{prefix}}" class="{{prefix}}" type="text" />',
               '</div>',
           '</div>',
           '<div class="control-group">',
               '<label class="control-label" for="cc-organization-{{prefix}}">Organization</label>',
               '<div class="controls">',
                 '<input id="cc-organization-{{prefix}}" class="{{prefix}}" type="text" />',
               '</div>',
           '</div>',
           '<div class="control-group">',
               '<label class="control-label" for="cc-email-{{prefix}}">Email</label>',
               '<div class="controls">',
                 '<input id="cc-email-{{prefix}}" class="{{prefix}}" type="email" />',
               '</div>',
           '</div>',
           '<div class="control-group">',
               '<label class="control-label" for="cc-phone-{{prefix}}">Phone</label>',
               '<div class="controls">',
                 '<input id="cc-phone-{{prefix}}" class="{{prefix}}" type="tel" />',
               '</div>',
           '</div>',
           '<div class="control-group">',
               '<label class="control-label" for="cc-address1-{{prefix}}">Address 1</label>',
               '<div class="controls">',
                 '<input id="cc-address1-{{prefix}}" class="{{prefix}}" type="text" />',
               '</div>',
           '</div>',
           '<div class="control-group">',
               '<label class="control-label" for="cc-address2-{{prefix}}">Address 2</label>',
               '<div class="controls">',
                 '<input id="cc-address2-{{prefix}}" class="{{prefix}}" type="text" />',
               '</div>',
           '</div>',
           '<div class="control-group">',
               '<label class="control-label" for="cc-city-{{prefix}}">City</label>',
               '<div class="controls">',
                 '<input id="cc-city-{{prefix}}" class="{{prefix}}" type="text" />',
               '</div>',
           '</div>',
           '<div class="control-group">',
               '<label class="control-label" for="cc-state-{{prefix}}">State/Province</label>',
               '<div class="controls">',
                 '<input id="cc-state-{{prefix}}" class="{{prefix}}" type="text" />',
               '</div>',
           '</div>',
           '<div class="control-group">',
               '<label class="control-label" for="cc-zip-{{prefix}}">Postal Code</label>',
               '<div class="controls">',
                 '<input id="cc-zip-{{prefix}}" class="{{prefix}}" type="text" />',
               '</div>',
           '</div>',
       '<div>'
    ].join('');
    

    function initWidget(input) {
        // create input form
        var prefix = input.attr('name');
        var ele = $(template.replace(/{{prefix}}/g,prefix));
        input.hide().after(ele);
        
        // add update handler
        ele.find('input').on('change', function(){
            var data = {};
            ele.find("."+prefix).each(function(){
                data[$(this).attr('id').replace('cc-','').replace('-'+prefix,'')] = $(this).val();
            });
            input.val(JSON.stringify(data));
        });
        
        // set default values
        try {
            var data = JSON.parse(input.val());
            for( var key in data ) $("#cc-"+key+"-"+prefix).val(data[key]);
        } catch(e) {}
    }
    
    return {
        initialize: function() {
            initWidget(this.el);
        },
        teardown: function () {
          // Called before a module is removed from the page.
        }
    }
});