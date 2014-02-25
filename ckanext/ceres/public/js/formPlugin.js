


// first, update all extra feilds and keep track of their id's
var eles = $('[extra-name]');
var map = {};
var count = 0;
for( var i = 0; i < eles.length; i++ ) {
    var ele = $(eles[i]);

    // set reference map for later
    map[ele.attr('extra-name')] = {
        name  : ele.attr('extra-name'),
        index : i,
        ele   : ele
    }

    // setup extra field elements
    ele.parent().append($('<input type="text" style="display:none" id="field-extras-'+(i+1)+'-key" name="extras__'+i+'__key" value="'+ele.attr('extra-name')+'" />'));

    // if the field is a check box, we need to fake the input
    if( ele.attr('type') == 'checkbox' ) {
        ele.attr('id','extras_checkbox_'+(i+1));
        ele.parent().append($('<input type="text" style="display:none" id="field-extras-'+(i+1)+'-value" name="extras__'+i+'__value" value="false" />'));
        ele.on('click', function(e){
            var val = $(this).is(':checked')+'';
            var index = $(this).attr('id').replace(/extras_checkbox_/,'');
            $('#field-extras-'+index+'-value').val(val);
        })

    } else {
        ele.attr('id', 'field-extras-'+(i+1)+'-value');
        ele.attr('name','extras__'+i+'__value');

        // handle the spatial plugin
        if ( ele.attr('extra-type') == 'spatial' ) {
            $('#'+ele.attr('extra-map')).attr('extra-id', ele.attr('id'));
        }
    }

    // set the labels 'for' attribute
    $('label[extra-label='+ele.attr('extra-name')+']').attr('for','field-extras-'+(i+1)+'-value');

    count++;
}

function setFormValue(obj, field) {
    // check for badness
    if( obj.ele.length == 0 ) return;

    if( obj.ele[0].nodeName == 'SELECT' || obj.ele[0].nodeName == 'INPUT' ) {
        obj.ele.val(field.value);

        // update the checkbox as well
        if( obj.ele.attr('type') == 'checkbox' ) {
            if( field.value == 'true' ) $('#extras_checkbox_'+(obj.index+1)).attr('checked',true);

        // handle the spatial plugin
        } else if ( obj.ele.attr('extra-type') == 'spatial' ) {
            $('#'+obj.ele.attr('extra-map')).attr('data-extent',field.value);
        }
    } else {
        alert('not sure how to set type: '+obj.ele.nodeName);
    }
}

function createHiddenFormInput(index, obj) {
    var form = $('.dataset-form');
    form.append($('<input type="text" style="display:none" id="field-extras-'+(index+1)+'-key" name="extras__'+index+'__key" value="'+obj.key+'" />'));
    form.append($('<input type="text" style="display:none" id="field-extras-'+(index+1)+'-value" name="extras__'+index+'__value" value="'+obj.value+'" />'));
}


if( window.__ckan_extra_fields ) {
    for( var i = 0; i < __ckan_extra_fields.length; i++ ) {
        if( map[__ckan_extra_fields[i].key] ) {
            setFormValue(map[__ckan_extra_fields[i].key], __ckan_extra_fields[i]);
        } else {
            createHiddenFormInput(count, __ckan_extra_fields[i]);
            count++;
        }
    }
}