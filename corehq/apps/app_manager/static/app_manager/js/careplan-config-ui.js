
var CareplanConfig = (function(){
    var Question = {
        mapping: {
            include: ['key', 'path']
        },
        wrap: function (data, transaction) {
            var self = ko.mapping.fromJS(data);
            self.transaction = transaction;

            self.validateQuestion = ko.computed(function () {
                if (self.path()) {
                    if (transaction.propertyPathCounts()[self.path()] > 1) {
                        return "Question is being used twice.";
                    }
                }
                return null;
            });
            self.validateKey = ko.computed(function () {
                if (self.path() || self.key()) {
                    if (transaction.propertyKeyCounts()[self.key()] > 1) {
                        return "Property updated by two questions";
                    }
                }
                return null;
            });
            self.validate = ko.computed(function() {
                return self.validateKey() || self.validateQuestion();
            })

            return self;
        }
    };

    var CaseProperty = {
        mapping: {
            include: ['key', 'path']
        },
        wrap: function (data, transaction) {
            var self = ko.mapping.fromJS(data, CaseProperty.mapping);
            self.transaction = transaction;
            self.isBlank = ko.computed(function () {
                return !self.key() && !self.path();
            });
            self.defaultKey = ko.computed(function () {
                var path = self.path() || '';
                var value = path.split('/');
                value = value[value.length-1];
                return value;
            });
            self.repeat_context = function () {
                return transaction.careplanConfig.get_repeat_context(self.path());
            };
            self.validateQuestion = ko.computed(function () {
                if (self.path()) {
                    if (transaction.propertyPathCounts()[self.path()] > 1) {
                        return "Question is being used twice.";
                    }
                }
            });
            self.validateKey = ko.computed(function () {
                if (self.path() || self.key()) {
                    if (transaction.propertyKeyCounts()[self.key()] > 1) {
                        return "Property updated by two questions";
                    } else if (transaction.careplanConfig.reserved_words.indexOf(self.key()) !== -1) {
                        return '<strong>' + self.key() + '</strong> is a reserved word';
                    } else if (self.repeat_context() && self.repeat_context() !== transaction.repeat_context()) {
                        return 'Inside the wrong repeat!'
                    }
                }
                return null;
            });
            self.validate = ko.computed(function() {
                return self.validateKey() || self.validateQuestion();
            })
            return self;
        }
    };

    var CareplanTransaction = {
        mapping: function (self) {
            return {
                include: [
                    'fixedQuestions',
                    'customCaseUpdates'
                ],
                fixedQuestions: {
                    create: function (options) {
                        return Question.wrap(options.data, self);
                    }
                },
                customCaseUpdates: {
                    create: function(options) {
                        return CaseProperty.wrap(options.data, self)
                    }
                }
            }
        },
        wrap: function (data, careplanConfig) {
            var self = {};
            ko.mapping.fromJS(data, CareplanTransaction.mapping(self), self);
            self.careplanConfig = careplanConfig;

            // link self.case_name to corresponding path observable
            // in case_properties for convenience
            try {
                self.case_name = _(self.fixedQuestions()).find(function (p) {
                    return p.name() === 'name_path';
                }).path;
            } catch (e) {
                self.case_name = null;
            }

            var count = function(accessor) {
                var count = {};
                var update_count = function(p) {
                    var key = p[accessor]();
                    if (!count.hasOwnProperty(key)) {
                        count[key] = 0;
                    }
                    return count[key] += 1;
                }
                _(self.fixedQuestions()).each(function (p) {
                    return update_count(p);
                });
                _(self.customCaseUpdates()).each(function (p){
                    return update_count(p);
                })
                return count;
            }

            self.propertyPathCounts = ko.computed(function () {
                return count('path');
            });

            self.propertyKeyCounts = ko.computed(function () {
                return count('key');
            });

            self.addProperty = function () {
                var property = CaseProperty.wrap({
                    path: '',
                    key: ''
                }, self);

                self.customCaseUpdates.push(property);
            };

            self.removeProperty = function (property) {
                self.customCaseUpdates.remove(property);
            };

            self.repeat_context = function () {
                return self.careplanConfig.get_repeat_context(self.case_name());
            };

            self.unwrap = function () {
                CareplanTransaction.unwrap(self);
            };

            return self;
        },
        unwrap: function (self) {
            return ko.mapping.toJS(self, CareplanTransaction.mapping(self));
        }
    }

    var Careplan = function(params){
        var self = this;
        self.home = params.home,
        self.edit = params.edit;
        self.save_url = params.save_url;
        self.questions = params.questions;
        self.reserved_words = params.reserved_words;
        self.transaction = CareplanTransaction.wrap({
            fixedQuestions: params.fixedQuestions,
            customCaseUpdates: params.customCaseUpdates
        }, self);

        var questionMap = {};
        _(self.questions).each(function (question) {
            questionMap[question.value] = question;
        });
        self.get_repeat_context = function(path) {
            if (path && questionMap[path]) {
                return questionMap[path].repeat;
            } else {
                return undefined;
            }
        };

        self.saveButton = COMMCAREHQ.SaveButton.init({
            unsavedMessage: "You have unsaved changes",
            save: function () {
                var transaction = CareplanTransaction.unwrap(self.transaction);
                self.saveButton.ajax({
                    type: 'post',
                    url: self.save_url,
                    data: {
                        fixedQuestions: JSON.stringify(transaction.fixedQuestions)
                    },
                    dataType: 'json',
                    success: function (data) {
                        COMMCAREHQ.app_manager.updateDOM(data.update);
                    }
                });
            }
        });

        self.validate = ko.computed(function(){
            var duplicate = _.find(_.values(self.transaction.propertyPathCounts()), function(count){
                return count > 1;
            });
            if (!duplicate) {
                duplicate = _.find(_.values(self.transaction.propertyPathCounts()), function(count){
                return count > 1;
            });
            }
            var isValid = duplicate === undefined;
            self.saveButton.fire(isValid ? 'enable' : 'disable');
            return  isValid;
        });

        self.change = function () {
            self.saveButton.fire('change');
        };

        self.init = function () {
            _.delay(function () {
                ko.applyBindings(self, self.home.get(0));
                self.home.on('textchange', 'input', self.change)
                     // all select2's are represented by an input[type="hidden"]
                     .on('change', 'select, input[type="hidden"]', self.change)
                     .on('click', 'a', self.change);
            });
        }
    };

    return {
        Careplan: Careplan
    };
}());
