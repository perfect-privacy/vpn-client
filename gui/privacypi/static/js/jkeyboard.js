
// the semi-colon before function invocation is a safety net against concatenated
// scripts and/or other plugins which may not be closed properly.
; (function ($, window, document, undefined) {

    // undefined is used here as the undefined global variable in ECMAScript 3 is
    // mutable (ie. it can be changed by someone else). undefined isn't really being
    // passed in so we can ensure the value of it is truly undefined. In ES5, undefined
    // can no longer be modified.

    // window and document are passed through as local variable rather than global
    // as this (slightly) quickens the resolution process and can be more efficiently
    // minified (especially when both are regularly referenced in your plugin).

    // Create the defaults once
    var pluginName = "jkeyboard",
        defaults = {
            layout: "english",
            selectable: ['azeri', 'english', 'german', 'russian'],
            input: $('#input'),
            customLayouts: {
                selectable: []
            },
        };


    var function_keys = {
        backspace: {
            text: '&nbsp;',
        },
        return: {
            text: 'Enter'
        },
        shift: {
            text: '&nbsp;'
        },
        space: {
            text: '&nbsp;'
        },
        numeric_switch: {
            text: '123',
            command: function () {
                pyview.createKeyboard('numeric');
                pyview.events();
            }
        },
        layout_switch: {
            text: '&nbsp;',
            command: function () {
                var l = pyview.toggleLayout();
                pyview.createKeyboard(l);
                pyview.events();
            }
        },
        character_switch: {
            text: 'ABC',
            command: function () {
                pyview.createKeyboard(layout);
                pyview.events();
            }
        },
        symbol_switch: {
            text: '#+=',
            command: function () {
                pyview.createKeyboard('symbolic');
                pyview.events();
            }
        }
    };


    var layouts = {
        azeri: [
            ['q', 'ü', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p', 'ö', 'ğ'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'ı', 'ə'],
            ['shift', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'ç', 'ş', 'backspace'],
            ['numeric_switch', 'layout_switch', 'space', 'return']
        ],
        english: [
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p',],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l',],
            ['shift', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'backspace'],
            ['numeric_switch', 'layout_switch', 'space', 'return']
        ],
        german: [
            ['q', 'w', 'e', 'r', 't', 'z', 'u', 'i', 'o', 'p','ü','ß'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l','ö','ä'],
            ['shift', 'y', 'x', 'c', 'v', 'b', 'n', 'm', 'backspace'],
            ['numeric_switch', 'layout_switch', 'space', 'return']
        ],
        russian: [
            ['й', 'ц', 'у', 'к', 'е', 'н', 'г', 'ш', 'щ', 'з', 'х'],
            ['ф', 'ы', 'в', 'а', 'п', 'р', 'о', 'л', 'д', 'ж', 'э'],
            ['shift', 'я', 'ч', 'с', 'м', 'и', 'т', 'ь', 'б', 'ю', 'backspace'],
            ['numeric_switch', 'layout_switch', 'space', 'return']
        ],
        numeric: [
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['-', '/', ':', ';', '(', ')', '$', '&', '@', '"'],
            ['symbol_switch', '.', ',', '?', '!', "'", 'backspace'],
            ['character_switch', 'layout_switch', 'space', 'return'],
        ],
        numbers_only: [
            ['1', '2', '3',],
            ['4', '5', '6',],
            ['7', '8', '9',],
            ['0', 'return', 'backspace'],
        ],
        symbolic: [
            ['[', ']', '{', '}', '#', '%', '^', '*', '+', '='],
            ['_', '\\', '|', '~', '<', '>'],
            ['numeric_switch', '.', ',', '?', '!', "'", 'backspace'],
            ['character_switch', 'layout_switch', 'space', 'return'],

        ]
    }

    var shift = false, capslock = false, layout = 'english', layout_id = 0;

    // The actual plugin constructor
    function Plugin(element, options) {
        pyview.element = element;
        // jQuery has an extend method which merges the contents of two or
        // more objects, storing the result in the first object. The first object
        // is generally empty as we don't want to alter the default options for
        // future instances of the plugin
        pyview.settings = $.extend({}, defaults, options);
        // Extend & Merge the cusom layouts
        layouts = $.extend(true, {}, pyview.settings.customLayouts, layouts);
        if (Array.isArray(pyview.settings.customLayouts.selectable)) {
            $.merge(pyview.settings.selectable, pyview.settings.customLayouts.selectable);
        }
        pyview._defaults = defaults;
        pyview._name = pluginName;
        pyview.init();
    }

    Plugin.prototype = {
        init: function () {
            layout = pyview.settings.layout;
            pyview.createKeyboard(layout);
            pyview.events();
        },

        setInput: function (newInputField) {
            pyview.settings.input = newInputField;
        },

        createKeyboard: function (layout) {
            shift = false;
            capslock = false;

            var keyboard_container = $('<ul/>').addClass('jkeyboard'),
                me = this;

            layouts[layout].forEach(function (line, index) {
                var line_container = $('<li/>').addClass('jline');
                line_container.append(me.createLine(line));
                keyboard_container.append(line_container);
            });

            $(pyview.element).html('').append(keyboard_container);
        },

        createLine: function (line) {
            var line_container = $('<ul/>');

            line.forEach(function (key, index) {
                var key_container = $('<li/>').addClass('jkey').data('command', key);

                if (function_keys[key]) {
                    key_container.addClass(key).html(function_keys[key].text);
                }
                else {
                    key_container.addClass('letter').html(key);
                }

                line_container.append(key_container);
            })

            return line_container;
        },

        events: function () {
            var letters = $(pyview.element).find('.letter'),
                shift_key = $(pyview.element).find('.shift'),
                space_key = $(pyview.element).find('.space'),
                backspace_key = $(pyview.element).find('.backspace'),
                return_key = $(pyview.element).find('.return'),

                me = this,
                fkeys = Object.keys(function_keys).map(function (k) {
                    return '.' + k;
                }).join(',');

            letters.on('click', function () {
                me.type((shift || capslock) ? $(this).text().toUpperCase() : $(this).text());
            });

            space_key.on('click', function () {
                me.type(' ');
            });

            return_key.on('click', function () {
                me.type("\n");
                me.settings.input.parents('form').submit();
            });

            backspace_key.on('click', function () {
                me.backspace();
            });

            shift_key.on('click', function () {
                if (shift) {
                    me.toggleShiftOff();
                } else {
                    me.toggleShiftOn();
                }
            }).on('dblclick', function () {
                me.toggleShiftOn(true);
            });


            $(fkeys).on('click', function (e) {
                //prevent bubbling to avoid side effects when used as floating keyboard which closes on click outside of keyboard container
                e.stopPropagation();
                
                var command = function_keys[$(this).data('command')].command;
                if (!command) return;

                command.call(me);
            });
        },

        type: function (key) {
            var input = pyview.settings.input,
                val = input.val(),
                input_node = input.get(0),
                start = input_node.selectionStart,
                end = input_node.selectionEnd;

            var max_length = $(input).attr("maxlength");
            if (start == end && end == val.length) {
                if (!max_length || val.length < max_length) {
                    input.val(val + key);
                }
            } else {
                var new_string = pyview.insertToString(start, end, val, key);
                input.val(new_string);
                start++;
                end = start;
                input_node.setSelectionRange(start, end);
            }

            input.trigger('focus');

            if (shift && !capslock) {
                pyview.toggleShiftOff();
            }
        },

        backspace: function () {
            var input = pyview.settings.input,
                input_node = input.get(0),
                start = input_node.selectionStart,
                val = input.val();    

            if (start > 0) {
                input.val(val.substring(0, start - 1) + val.substring(start));
                input.trigger('focus');
                input_node.setSelectionRange(start - 1, start - 1);
            }
            else {
                input.trigger('focus');
                input_node.setSelectionRange(0, 0);
            }
	    },

        toggleShiftOn: function (lock) {
            var letters = $(pyview.element).find('.letter'),
                shift_key = $(pyview.element).find('.shift');

            letters.addClass('uppercase');
            shift_key.addClass('active');
            if (typeof lock !== 'undefined' && lock) {
                shift_key.addClass('lock');
                capslock = true;
            }
            shift = true;
        },

        toggleShiftOff: function () {
            var letters = $(pyview.element).find('.letter'),
                shift_key = $(pyview.element).find('.shift');

            letters.removeClass('uppercase');
            shift_key.removeClass('active lock');
            shift = capslock = false;
        },

        toggleLayout: function () {
            layout_id = layout_id || 0;
            var plain_layouts = pyview.settings.selectable;
            layout_id++;

            var current_id = layout_id % plain_layouts.length;
            return plain_layouts[current_id];
        },

        insertToString: function (start, end, string, insert_string) {
            return string.substring(0, start) + insert_string + string.substring(end, string.length);
        }
    };


    var methods = {
        init: function(options) {
            if (!pyview.data("plugin_" + pluginName)) {
                pyview.data("plugin_" + pluginName, new Plugin(this, options));
            }
        },
        setInput: function(content) {
            pyview.data("plugin_" + pluginName).setInput($(content));
        },
        setLayout: function(layoutname) {
            // change layout if it is not match current
            object = pyview.data("plugin_" + pluginName);
            if (typeof(layouts[layoutname]) !== 'undefined' && object.settings.layout != layoutname) {
                object.settings.layout = layoutname;
                object.createKeyboard(layoutname);
                object.events();
            };
        },
    };

    $.fn[pluginName] = function (methodOrOptions) {
        if (methods[methodOrOptions]) {
            return methods[methodOrOptions].apply(pyview.first(), Array.prototype.slice.call( arguments, 1));
        } else if (typeof methodOrOptions === 'object' || ! methodOrOptions) {
            // Default to "init"
            return methods.init.apply(pyview.first(), arguments);
        } else {
            $.error('Method ' +  methodOrOptions + ' does not exist on jQuery.jkeyboard');
        }
    };

})(jQuery, window, document);
