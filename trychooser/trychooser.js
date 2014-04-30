$(document).ready(function() {
    // Call out nondefault options
    $('<span> (not run by default)</span>')
        .addClass('info')
        .insertAfter($('.nondefault').parent());

    // Several subsections are headed by all/none selectors. Make them control
    // their dependents

    // If the all-selector is checked, then force all default items to be checked
    var suppress_loop = false;
    $('.all-selector').change(function() {
        if ($(this).prop('checked')) {
            suppress_loop = true;
            var group = $(this).closest('.option-group');
            group.find(':checkbox:not(.group-selector):not(.nondefault)')
                .prop('checked', true);
            group.find('.none-selector')
                .prop('checked', false);
            suppress_loop = false;
        }
    });

    // If the none-selector is checked, then force all items to be unchecked
    $('.none-selector').change(function() {
        if ($(this).prop('checked')) {
            suppress_loop = true;
            var group = $(this).closest('.option-group');
            group.find(':checkbox:not(.group-selector)')
                .prop('checked', false);
            group.find('.all-selector')
                .prop('checked', false);
            suppress_loop = false;
        }
    });

    // Handle subgroups (eg mochitests-all).
    $('.subgroup-all-selector').change(function() {
        if ($(this).prop('checked')) {
            $(this).closest('.option-subgroup').find(':checkbox:not(.subgroup-selector):not(.nondefault)')
                .prop('checked', true);
        }
    });

    // This must come before the regular checkboxes, so that the All selector
    // is set in time to collapse the toplevel 'all'.
    $('.option-subgroup').find(':checkbox:not(.subgroup-selector)').change(function() {
        var subgroup = $(this).closest('.option-subgroup');
        var unchecked_defaults =
            subgroup.find(':checkbox:not(.subgroup-selector):not(:checked):not(.nondefault)');
        subgroup.find('.subgroup-selector').prop('checked', unchecked_defaults.length == 0);
    });

    // Make all option-group descendant checkboxes control the group-selectors
    $('.option-group').find(':checkbox:not(.group-selector)').change(function() {
        if (suppress_loop) return;
        var group = $(this).closest('.option-group');

        var checked = group.find(':checkbox:not(.group-selector):checked');
        group.find('.none-selector').prop('checked', checked.length == 0);

        var unchecked_defaults =
            group.find(':checkbox:not(.group-selector):not(:checked):not(.nondefault)');
        group.find('.all-selector').prop('checked', unchecked_defaults.length == 0);
    });

    // Force initial update
    $('.all-selector:checked').change();
    $('.none-selector:checked').change();

    // Selecting anything should update the try syntax
    $(':checkbox').change(setresult);
    $(':radio').change(setresult);

    // Initialize the try syntax
    setresult();
});

function resolveFilters(filters) {
    // The linux32 hack requires cancelling out mutually-exclusive options
    var want = {};
    for (var i in filters) {
        if (filters[i].charAt(0) != '-') {
            want[filters[i]] = true;
        }
    }
    for (var i in filters) {
        if (filters[i].charAt(0) == '-') {
            var name = filters[i].substring(1);
            if (name in want)
                delete want[name];
            else
                want[filters[i]] = true;
        }
    }
    return Object.keys(want);
}

function setresult() {
    var value = 'try: ';
    var args = [];

    args.push('try:');

    $('.option-radio[try-section]').each(function() {
        var arg = '-' + $(this).attr('try-section') + ' ';
        arg += $(this).find(':checked').attr('value');
        args.push(arg);
    });

    $('.option-email').each(function() {
        var arg = $(this).find(':checked').attr('value');
        if (arg != 'on')
            args.push(arg);
    });

    var have_projects = {};
    $('.option-group[try-section]').each(function() {
        var tryopt = $(this).attr('try-section');
        var arg = '-' + tryopt + ' ';
        var names = [];
        if ($(this).find('.none-selector:checked').length > 0) {
            names = ['none'];
        } else if ($(this).find('.all-selector:checked').length > 0) {
            names = ['all'];
        } else {
            var group = $(this).closest('.option-group');
            var options;
            if (group.find('.subgroup-all-selector:checked').length > 0) {
                // Special-case. We need to collapse things into a subgroup "all" value
                options = group.find(':checked:not(.group-selector):not(.option-subgroup *)')
                    .add('.subgroup-all-selector', group);
            } else {
                options = group.find(':checked:not(.group-selector):not(.subgroup-selector):not(.nondefault)');
            }
            options.each(function(i,elt){
              names.push($(elt).attr('value'));
              var project = $(elt).attr('data-project');
              if (project)
                have_projects[project] = true;
            });
        }

        // Add in the nondefault builders
        $(this).find(':checked.nondefault').each(function(i,elt) {
            names.push($(elt).attr('value'));
        });

        // If you specifically request a b2g or android build platform, then
        // disable the filtering. This does not apply when you just pick 'all'.
        var disable_filters = ("b2g" in have_projects) || ("android" in have_projects);
        $('[try-filter=' + tryopt + ']').prop('disabled', disable_filters);
        $('[try-filter=' + tryopt + ']').fadeTo(0, disable_filters ? 0.5 : 1.0);

        var filters = [];
        $('[try-filter=' + tryopt + '] :checked').each(function () {
          filters.push.apply(filters, $(this).attr('value').split(','));
        });
        if (filters.length > 0 && !disable_filters) {
          filters = resolveFilters(filters).join(',');
          names = names.map(function (n) { return n + '[' + filters + ']'; });
        }

        arg += names.join(',');
        args.push(arg);
    });

    if ($('.profile').is(':checked')) {
      args.push('mozharness: --spsProfile');
    }

    value = args.join(' ');

    if (value.match(/-p none/)) {
        value = "(NO JOBS CHOSEN)";
        $('#platforms-none').addClass('attention');
    } else {
        $('#platforms-none').removeClass('attention');
    }

    $('.result_value').val(value);
}
