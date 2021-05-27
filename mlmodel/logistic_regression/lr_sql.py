from collections import Iterable
from sklearn.linear_model import LogisticRegression


class LogisticRegressionSQL(object):
    """
    This class implements the SQL wrapper for the Sklearn's LogisticRegression.
    """

    def reset_optimization(self):
        pass

    @staticmethod
    def get_params(lr):
        """
        This method extracts from the LogisticRegression the fitted parameters (i.e., weights and intercepts for each
        class)

        :param lr: the fitted Sklean LogisticRegression object
        :return: Python dictionary containing the fitted parameters extracted from the Sklearn's LogisticRegression
        """

        if not isinstance(lr, LogisticRegression):
            raise TypeError("Wrong data type for parameter lr. Only Sklearn LogisticRegression data type is allowed.")

        weights = lr.coef_
        bias = lr.intercept_

        return {"weights": weights, "bias": bias}

    @staticmethod
    def _generate_linear_combination(weights, bias, columns):
        """
        This method generates the linear combination component of the LogisticRegression function.

        :param weights: the weights for a target class
        :param bias: the bias for a target class
        :param columns: the feature names
        :return: the portion of SQL query responsible for the application of the linear combination component of the
                 LogisticRegression function
        """

        if not isinstance(weights, Iterable):
            raise TypeError("Wrong data type for parameter weights. Only iterable data type is allowed.")

        if not isinstance(bias, float):
            raise TypeError("Wrong data type for parameter bias. Only float data type is allowed.")

        if not isinstance(columns, Iterable):
            raise TypeError("Wrong data type for parameter columns. Only iterable data type is allowed.")

        for weight in weights:
            if not isinstance(weight, float):
                raise TypeError("Wrong data type for weights elements. Only float data type is allowed.")

        for col in columns:
            if not isinstance(col, str):
                raise TypeError("Wrong data type for columns elements. Only string data type is allowed.")

        query = ""
        for i in range(len(columns)):
            c = columns[i]
            query += "(`{}`*{}) + ".format(c, weights[i])
        query = "{} {}".format(query, bias)

        return query

    @staticmethod
    def _get_raw_query(weights, bias, features, table_name, class_labels):
        """
        This method creates the SQL query responsible for the application of the Logistic Regression function.

        :param weights: the weights
        :param bias: the biases
        :param features: the feature names
        :param table_name: the name of the table or the subquery where to read the data
        :param class_labels: the labels of the class attribute
        :return: the SQL query responsible for the application of the Logistic Regression function
        """

        if not isinstance(weights, Iterable):
            raise TypeError("Wrong data type for parameter weights. Only iterable data type is allowed.")

        if not isinstance(bias, Iterable):
            raise TypeError("Wrong data type for parameter bias. Only iterable data type is allowed.")

        if not isinstance(features, Iterable):
            raise TypeError("Wrong data type for parameter columns. Only iterable data type is allowed.")

        for f in features:
            if not isinstance(f, str):
                raise TypeError("Wrong data type for feature elements. Only string data type is allowed.")

        if table_name is not None:
            if not isinstance(table_name, str):
                raise TypeError("Wrong data type for parameter table_name. Only string data type is allowed.")

        if not isinstance(class_labels, Iterable):
            raise TypeError("Wrong data type for parameter class_labels. Only iterable data type is allowed.")

        query_internal = "SELECT "
        wildcard = "class_"

        for i in range(len(weights)):
            w = weights[i]
            b = bias[i]

            q = LogisticRegressionSQL._generate_linear_combination(w, b, features)

            query_internal += "({}) AS {}{},".format(q, wildcard, i)

        query_internal = query_internal[:-1] # remove the last ','

        query_internal += "\n FROM {}".format(table_name)

        query_internal = " ( {} ) AS F ".format(query_internal)

        query = "SELECT "

        if len(class_labels) > 2:

            sum_query = "("
            for i in range(len(bias)):
                sum_query += "EXP({}{})+".format(wildcard, i)
            sum_query = sum_query[:-1] # remove the last '+'
            sum_query += ")"

            for i in range(len(bias)):
                query += "(" + "EXP({}{}) / {} ) AS {}{},".format(wildcard, i, sum_query, wildcard, i)

            query = query[:-1] # remove the last ','
            query = "{}\n FROM {}".format(query, query_internal)

            case_stm = "CASE"
            for i in range(len(class_labels)):
                case_stm += " WHEN "
                for j in range(len(class_labels)):
                    if j == i:
                        continue
                    case_stm += "{}{} >= {}{} AND ".format(wildcard, i, wildcard, j)
                case_stm = case_stm[:-5] # remove the last ' AND '
                case_stm += " THEN {}\n".format(class_labels[i])
            case_stm += "END AS Score"

            final_query = "SELECT {} FROM ({}) AS F".format(case_stm, query)
        else:
            score_to_class_query = "SELECT CASE WHEN -1.0*{}0 > 500 THEN 0 ELSE".format(wildcard)
            score_to_class_query += " 1.0/(1.0+EXP(-1.0*{}0)) END AS PROB_0".format(wildcard)
            score_to_class_query += " FROM {}".format(query_internal)

            final_query = "SELECT CASE WHEN PROB_0 > (1-PROB_0) THEN 1 ELSE 0 END AS Score FROM ({}) AS F".format(
                score_to_class_query)

        return final_query

    def query(self, lr, features, table_name, class_labels=None):
        """
        This method creates the SQL query that performs the LogisticRegression inference.

        :param lr: the fitted Sklearn LogisticRegression object
        :param features: the list of features
        :param table_name: the name of the table or the subquery where to read the data
        :param class_labels: the labels of the class attribute
        :return: the SQL query that implements the Logistic Regression inference
        """

        if not isinstance(lr, LogisticRegression):
            raise TypeError("Wrong data type for parameter lr. Only Sklearn LogisticRegression data type is allowed.")

        if not isinstance(features, Iterable):
            raise TypeError("Wrong data type for parameter features. Only iterable data type is allowed.")

        for f in features:
            if not isinstance(f, str):
                raise TypeError("Wrong data type for single features. Only string data type is allowed.")

        if not isinstance(table_name, str):
            raise TypeError("Wrong data type for parameter table_name. Only string data type is allowed.")

        if class_labels is not None:
            if not isinstance(class_labels, Iterable):
                raise TypeError("Wrong data type for parameter class_labels. Only iterable data type is allowed.")

        params = LogisticRegressionSQL.get_params(lr)
        weights = params["weights"]
        bias = params["bias"]
        if not class_labels:
            class_labels = list(lr.classes_)

        # create the SQL query that implements the LogisticRegression inference
        query = LogisticRegressionSQL._get_raw_query(weights, bias, features, table_name, class_labels)

        return query
